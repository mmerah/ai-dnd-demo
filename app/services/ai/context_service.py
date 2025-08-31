"""Service for building AI context following Single Responsibility."""

from app.interfaces.services import (
    IItemRepository,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.models.game_state import GameState
from app.models.quest import ObjectiveStatus
from app.models.scenario import Scenario


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

        # Add scenario context if available
        if game_state.scenario_id and game_state.current_location_id:
            scenario = self.scenario_service.get_scenario(game_state.scenario_id)
            if scenario:
                # Get base scenario context
                scenario_context = self.scenario_service.get_scenario_context_for_ai(
                    scenario,
                    game_state.current_location_id,
                )
                context_parts.append(scenario_context)

                # Add enhanced location details
                location_context = self._build_location_context(game_state, scenario)
                if location_context:
                    context_parts.append(location_context)

                # Add quest context
                quest_context = self._build_quest_context(game_state, scenario)
                if quest_context:
                    context_parts.append(quest_context)

        # Add current game state
        char = game_state.character
        context_parts.append(
            f"""Current State:
- Character: {char.name} ({char.race} {char.class_name} Level {char.level})
- HP: {char.hit_points.current}/{char.hit_points.maximum}, AC: {char.armor_class}
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
        if char.spellcasting and char.spellcasting.spells_known:
            spell_context = self._build_spell_context(char.spellcasting.spells_known)
            if spell_context:
                context_parts.append(spell_context)

        return "\n\n".join(context_parts)

    def _build_location_context(self, game_state: GameState, scenario: Scenario) -> str | None:
        """Build enhanced location context with connections, encounters, and loot."""
        if not game_state.current_location_id:
            return None

        location = scenario.get_location(game_state.current_location_id)
        if not location:
            return None

        location_state = game_state.get_location_state(game_state.current_location_id)
        context_parts = ["Enhanced Location Details:"]

        # Location state information
        context_parts.append(f"- Current Location ID: {game_state.current_location_id}")
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

        # Potential encounters (not yet completed)
        uncompleted_encounters = [
            enc for enc in location.encounters if enc.id not in location_state.completed_encounters
        ]
        if uncompleted_encounters:
            context_parts.append("\nPotential Encounters:")
            for enc in uncompleted_encounters[:3]:  # Limit to avoid too much context
                context_parts.append(f"  - {enc.type} [ID: {enc.id}]: {enc.description[:50]}...")

        # Available loot (if any not taken)
        if location.loot_table:
            available_loot = [loot for loot in location.loot_table if not loot.found]
            if available_loot:
                context_parts.append("\nPotential Items (not yet found):")
                for loot in available_loot[:3]:
                    if not loot.hidden:
                        context_parts.append(f"  - {loot.item_name}")

        # NPCs in location
        if location_state.npcs_present:
            context_parts.append(f"\nNPCs Here: {', '.join(location_state.npcs_present)}")

        return "\n".join(context_parts)

    def _build_quest_context(self, game_state: GameState, scenario: Scenario) -> str | None:
        """Build quest context with active quests and objectives."""
        if not game_state.active_quests:
            return None

        context_parts = ["Active Quests:"]

        for quest in game_state.active_quests:
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
            if (
                quest_def.id not in [q.id for q in game_state.active_quests]
                and quest_def.id not in game_state.completed_quest_ids
                and quest_def.is_available(game_state.completed_quest_ids)
            ):
                available_quests.append(f"{quest_def.name} [ID: {quest_def.id}]")

        if available_quests:
            context_parts.append(f"\nAvailable New Quests: {', '.join(available_quests[:2])}")

        return "\n".join(context_parts)

    def _build_npc_context(self, game_state: GameState) -> str:
        """Build detailed NPC context with abilities."""
        npc_lines = ["NPCs Present:"]

        for npc in game_state.npcs:
            # Basic info
            npc_info = f"  • {npc.name}: HP {npc.hit_points.current}/{npc.hit_points.maximum}, AC {npc.armor_class}"

            # Add conditions if any
            if npc.conditions:
                npc_info += f" [{', '.join(npc.conditions)}]"

            npc_lines.append(npc_info)

            # If NPC has notable abilities, mention them briefly
            if npc.abilities:
                ability_summary = (
                    f"    Abilities - STR: {npc.abilities.STR}, DEX: {npc.abilities.DEX}, CON: {npc.abilities.CON}"
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
                context_parts.append(f"  {marker} {participant.initiative:2d}: {participant.name}{player_tag}")

        return "\n".join(context_parts)

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
