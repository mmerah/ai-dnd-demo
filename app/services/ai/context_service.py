"""Service for building AI context following Single Responsibility."""

from app.interfaces.services import (
    IItemRepository,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.models.entity import EntityType
from app.models.game_state import GameState
from app.models.quest import ObjectiveStatus
from app.models.scenario import ScenarioSheet

# TODO: Could just deep-load GameState and Scenario no ? Does it need to be that complicated ?


class ContextService:
    """Service for building AI context following Single Responsibility."""

    def __init__(
        self,
        scenario_service: IScenarioService,
        item_repository: IItemRepository | None = None,
        monster_repository: IMonsterRepository | None = None,
        spell_repository: ISpellRepository | None = None,
    ):
        self.scenario_service = scenario_service
        self.item_repository = item_repository
        self.monster_repository = monster_repository
        self.spell_repository = spell_repository

    def build_context(self, game_state: GameState) -> str:
        """Build enhanced context string from game state."""
        context_parts = []

        # Add scenario context if available and in known location
        if game_state.scenario_instance.is_in_known_location():
            scenario = game_state.scenario_instance.sheet
            # Get base scenario context
            scenario_context = self.scenario_service.get_scenario_context_for_ai(
                scenario,
                game_state.scenario_instance.current_location_id,
            )
            context_parts.append(scenario_context)

            # Add enhanced location details
            location_context = self._build_location_context(game_state, scenario)
            if location_context:
                context_parts.append(location_context)

            # Add NPCs at current location
            npcs_context = self._build_npcs_at_location_context(game_state)
            if npcs_context:
                context_parts.append(npcs_context)

            # Add Monsters present at current location (runtime instances)
            monsters_context = self._build_monsters_at_location_context(game_state)
            if monsters_context:
                context_parts.append(monsters_context)

            # Add quest context
            quest_context = self._build_quest_context(game_state, scenario)
            if quest_context:
                context_parts.append(quest_context)

        # Add current game state
        char_sheet = game_state.character.sheet
        char_state = game_state.character.state
        class_display = char_sheet.class_display
        context_parts.append(
            f"""Current State:
- Character: {char_sheet.name} ({char_sheet.race} {class_display} Level {char_state.level})
- HP: {char_state.hit_points.current}/{char_state.hit_points.maximum}, AC: {char_state.armor_class}
- Location: {game_state.location}
- Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}""",
        )

        # Add detailed NPC information
        if game_state.npcs:
            npc_context = self._build_npc_context(game_state)
            context_parts.append(npc_context)

        # Add combat context
        if game_state.combat:
            combat_context = self._build_combat_context(game_state)
            context_parts.append(combat_context)

        # Add character spell context if relevant
        if char_state.spellcasting and char_state.spellcasting.spells_known:
            spell_context = self._build_spell_context(char_state.spellcasting.spells_known)
            if spell_context:
                context_parts.append(spell_context)

        # Add player's inventory with exact item names to guide tools
        inventory_context = self._build_inventory_context(game_state)
        if inventory_context:
            context_parts.append(inventory_context)

        # Add available items context for NPCs
        if game_state.npcs:
            item_context = self._build_npc_items_context(game_state)
            if item_context:
                context_parts.append(item_context)

        return "\n\n".join(context_parts)

    def _build_location_context(self, game_state: GameState, scenario: ScenarioSheet) -> str | None:
        """Build enhanced location context with connections, encounters, and loot."""
        if not game_state.scenario_instance.is_in_known_location():
            return None
        loc_id = game_state.scenario_instance.current_location_id

        location = scenario.get_location(loc_id)
        if not location:
            return None

        location_state = game_state.get_location_state(loc_id)
        context_parts = ["Enhanced Location Details:"]

        # Location state information
        context_parts.append(f"- Current Location ID: {loc_id}")
        context_parts.append(f"- Danger Level: {location_state.danger_level.value}")
        context_parts.append(f"- Visited: {location_state.times_visited} time(s)")

        # Available connections with requirements
        if location.connections:
            context_parts.append("\nAvailable Exits:")
            for conn in location.connections:
                if conn.is_visible:
                    target_loc = scenario.get_location(conn.to_location_id)
                    if target_loc:
                        exit_desc = f"  - {conn.description} to {target_loc.name} [ID: {conn.to_location_id}]"
                        if conn.requirements:
                            req_status = "✓" if conn.can_traverse() else "✗"
                            exit_desc += f" [{req_status}]"
                        context_parts.append(exit_desc)

        # Notable monsters present
        if location.notable_monsters:
            context_parts.append("\nNotable Threats:")
            for nm in location.notable_monsters:
                try:
                    context_parts.append(f"  - {nm.display_name}: {nm.description or ''}")
                except Exception:
                    continue

        # Potential encounters (not yet completed)
        uncompleted_encounter_ids = [
            eid for eid in location.encounter_ids if eid not in location_state.completed_encounters
        ]
        if uncompleted_encounter_ids:
            context_parts.append("\nPotential Encounters:")
            for eid in uncompleted_encounter_ids[:5]:  # Limit to avoid too much context
                enc = scenario.get_encounter_by_id(eid)
                if enc:
                    context_parts.append(f"  - {enc.type} [ID: {enc.id}]: {enc.description[:50]}...")

        # Available loot (if any not taken)
        if location.loot_table:
            available_loot = [loot for loot in location.loot_table if not loot.found]
            if available_loot:
                context_parts.append("\nPotential Items (not yet found):")
                for loot in available_loot[:3]:
                    if not loot.hidden:
                        if self.item_repository and self.item_repository.validate_reference(loot.item_name):
                            context_parts.append(f"  - {loot.item_name} (use exact name: '{loot.item_name}')")
                        else:
                            context_parts.append(f"  - {loot.item_name}")

        return "\n".join(context_parts)

    def _build_monsters_at_location_context(self, game_state: GameState) -> str | None:
        """Build context for monsters present at current location (runtime instances)."""
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
        monsters_here = [m for m in game_state.monsters if m.current_location_id == current_loc_id and m.is_alive()]

        if not monsters_here:
            return None

        lines = ["Monsters Present (use IDs for tools):"]
        for m in monsters_here:
            st = m.state
            lines.append(
                f"  • {m.sheet.name} [ID: {m.instance_id}]: HP {st.hit_points.current}/{st.hit_points.maximum}, AC {st.armor_class}"
            )

        return "\n".join(lines)

    def _build_npcs_at_location_context(self, game_state: GameState) -> str | None:
        """Build context for NPCs present at current location."""
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id

        # Filter NPCs by current location
        npcs_here = [npc for npc in game_state.npcs if npc.current_location_id == current_loc_id]

        if not npcs_here:
            return None

        context_parts = ["NPCs at this location:"]
        for npc in npcs_here:
            npc_info = f"- {npc.sheet.display_name} ({npc.sheet.role}): {npc.sheet.description}"
            if npc.attitude:
                npc_info += f" [Attitude: {npc.attitude}]"
            context_parts.append(npc_info)

        return "\n".join(context_parts)

    def _build_quest_context(self, game_state: GameState, scenario: ScenarioSheet) -> str | None:
        """Build quest context with active quests and objectives."""
        if not game_state.scenario_instance.active_quests:
            return None

        context_parts = ["Active Quests:"]

        for quest in game_state.scenario_instance.active_quests:
            context_parts.append(f"\n• {quest.name} [ID: {quest.id}] ({quest.get_progress_percentage():.0f}% complete)")

            # Show active objectives with their IDs
            active_objectives = quest.get_active_objectives()
            if active_objectives:
                context_parts.append("  Objectives:")
                for obj in active_objectives[:3]:  # Limit objectives shown
                    status_marker = "○" if obj.status == ObjectiveStatus.PENDING else "◐"
                    context_parts.append(f"    {status_marker} {obj.description} [ID: {obj.id}]")

        # Mention available quests based on prerequisites with their IDs
        available_quests = []
        for quest_def in scenario.quests:
            active_ids = [q.id for q in game_state.scenario_instance.active_quests]
            completed_ids = game_state.scenario_instance.completed_quest_ids
            if (
                quest_def.id not in active_ids
                and quest_def.id not in completed_ids
                and quest_def.is_available(completed_ids)
            ):
                available_quests.append(f"{quest_def.name} [ID: {quest_def.id}]")

        if available_quests:
            context_parts.append(f"\nAvailable New Quests: {', '.join(available_quests[:2])}")

        return "\n".join(context_parts)

    def _build_npc_context(self, game_state: GameState) -> str:
        """Build detailed NPC context with abilities."""
        if not game_state.scenario_instance.is_in_known_location():
            return ""

        current_loc_id = game_state.scenario_instance.current_location_id
        npcs_here = [npc for npc in game_state.npcs if npc.current_location_id == current_loc_id]

        if not npcs_here:
            return ""

        npc_lines = ["NPCs Present (Detailed):"]

        for npc in npcs_here:
            # Basic info
            npc_name = npc.sheet.character.name
            npc_state = npc.state
            npc_info = (
                f"  • {npc_name} [ID: {npc.instance_id}]: "
                f"HP {npc_state.hit_points.current}/{npc_state.hit_points.maximum}, AC {npc_state.armor_class}"
            )

            # Add conditions if any
            if npc_state.conditions:
                npc_info += f" [{', '.join(npc_state.conditions)}]"

            npc_lines.append(npc_info)

            # If NPC has notable abilities, mention them briefly
            ability_summary = (
                f"    Abilities - STR: {npc_state.abilities.STR}, "
                f"DEX: {npc_state.abilities.DEX}, CON: {npc_state.abilities.CON}"
            )
            npc_lines.append(ability_summary)

        return "\n".join(npc_lines)

    def _build_combat_context(self, game_state: GameState) -> str:
        """Build detailed combat context."""
        if not game_state.combat:
            return ""

        combat = game_state.combat
        current_turn = combat.get_current_turn()

        context_parts = [f"Combat Status - Round {combat.round_number}:"]

        if current_turn:
            context_parts.append(f"Current Turn: {current_turn.name}")

        # Initiative order
        context_parts.append("\nInitiative Order:")
        for participant in combat.participants:
            if participant.is_active:
                marker = "→" if current_turn and participant.name == current_turn.name else " "
                player_tag = " [PLAYER]" if participant.is_player else ""
                context_parts.append(
                    f"  {marker} {participant.initiative:2d}: {participant.name}{player_tag} (ID: {participant.entity_id})"
                )

        # Monsters in Combat (detailed)
        monsters_block = self._build_monsters_in_combat_context(game_state)
        if monsters_block:
            context_parts.append("\n" + monsters_block)

        return "\n".join(context_parts)

    def _build_monsters_in_combat_context(self, game_state: GameState) -> str | None:
        """List monsters currently participating in combat with stats and initiative."""
        if not game_state.combat:
            return None
        combat = game_state.combat
        rows: list[str] = []
        for p in combat.participants:
            etype = p.entity_type.value if hasattr(p.entity_type, "value") else str(p.entity_type)
            if etype != EntityType.MONSTER.value:
                continue
            monster = game_state.get_entity_by_id(EntityType.MONSTER, p.entity_id)
            if not monster:
                continue
            st = monster.state
            status = "ACTIVE" if p.is_active else "INACTIVE"
            cond = f" [{', '.join(st.conditions)}]" if st.conditions else ""
            rows.append(
                f"  • {p.name} [ID: {p.entity_id}] — Init {p.initiative}, {status}; HP {st.hit_points.current}/{st.hit_points.maximum}, AC {st.armor_class}{cond}"
            )
        if not rows:
            return None
        return "Monsters in Combat:\n" + "\n".join(rows)

    def _build_spell_context(self, spells: list[str]) -> str | None:
        """Build spell context with descriptions if data service available."""
        if not self.spell_repository or not spells:
            return None

        context_parts = ["Known Spells:"]

        for spell_name in spells[:5]:  # Limit to 5 spells to avoid context overflow
            spell_def = self.spell_repository.get(spell_name)
            if spell_def:
                context_parts.append(f"  • {spell_name} (Level {spell_def.level}): {spell_def.description[:100]}...")
            else:
                context_parts.append(f"  • {spell_name}")

        return "\n".join(context_parts)

    def _build_inventory_context(self, game_state: GameState) -> str | None:
        """List player's inventory with exact item names and quantities."""
        inv = game_state.character.state.inventory
        if not inv:
            return None

        lines = ["Your Inventory (use exact names shown):"]
        # Show up to 20 entries to avoid too much context
        for item in inv[:20]:
            lines.append(f"  • {item.name} x{item.quantity}")
        return "\n".join(lines)

    def _build_npc_items_context(self, game_state: GameState) -> str | None:
        """Build context about items NPCs have available for trade/giving."""
        if not game_state.npcs or not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
        npcs_here = [npc for npc in game_state.npcs if npc.current_location_id == current_loc_id]

        if not npcs_here:
            return None

        items_mentioned: set[str] = set()
        context_parts: list[str] = []

        for npc in npcs_here:
            npc_items: list[str] = []
            for item in npc.state.inventory:
                if item.name not in items_mentioned:
                    items_mentioned.add(item.name)
                    # Show the exact name the AI should use
                    if self.item_repository:
                        # Check if this is a valid item and get its proper reference
                        if self.item_repository.validate_reference(item.name):
                            npc_items.append(f"{item.name} (use exact name: '{item.name}')")
                    else:
                        npc_items.append(item.name)

            if npc_items:
                if not context_parts:
                    context_parts.append("NPC Available Items (use exact names shown):")
                context_parts.append(f"  {npc.sheet.character.name} has: {', '.join(npc_items)}")

        return "\n".join(context_parts) if context_parts else None
