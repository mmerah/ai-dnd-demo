"""Builder for NPCs at current location."""

from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, ContextBuilder


class NPCLocationContextBuilder(ContextBuilder):
    """Build comprehensive NPC context for current location.

    Party members: Minimal info (name + ID + marker) since full details are in party context
    Non-party NPCs: Full details including stats, items, and conditions
    """

    MAX_ITEMS_PER_NPC = 10

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
        npcs_here = [npc for npc in game_state.npcs if npc.current_location_id == current_loc_id]
        if not npcs_here:
            return None

        lines = ["NPCs Present:"]

        for npc in npcs_here:
            is_party_member = game_state.party.has_member(npc.instance_id)

            if is_party_member:
                # Party members: minimal info (full details in party context)
                lines.append(f"- {npc.display_name} [{npc.instance_id}] [IN PARTY]")
            else:
                # Non-party NPCs: full details
                lines.extend(self._build_npc_details(npc, context))

        return "\n".join(lines)

    def _build_npc_details(self, npc: NPCInstance, context: BuildContext) -> list[str]:
        """Build detailed information for a non-party NPC.

        Args:
            npc: The NPC instance
            context: Builder dependencies

        Returns:
            List of formatted detail lines
        """
        lines = []
        npc_sheet = npc.sheet
        npc_state = npc.state

        # Header line: Name, ID, role, description, attitude
        header = f"- {npc.display_name} [{npc.instance_id}] ({npc_sheet.role}): {npc_sheet.description}"
        if npc.attitude:
            header += f" [{npc.attitude}]"
        lines.append(header)

        # Stats: Level, HP, AC, abilities
        abilities = npc_state.abilities
        stats_line = (
            f"  Lvl {npc_state.level} | "
            f"HP {npc_state.hit_points.current}/{npc_state.hit_points.maximum} | "
            f"AC {npc_state.armor_class} | "
            f"STR {abilities.STR} DEX {abilities.DEX} CON {abilities.CON} "
            f"INT {abilities.INT} WIS {abilities.WIS} CHA {abilities.CHA}"
        )
        lines.append(stats_line)

        # Conditions
        if npc_state.conditions:
            lines.append(f"  Conditions: {', '.join(npc_state.conditions)}")

        # Items
        if npc_state.inventory:
            items_to_show = npc_state.inventory[: self.MAX_ITEMS_PER_NPC]
            valid_items = [
                item.index for item in items_to_show if context.item_repository.validate_reference(item.index)
            ]
            if valid_items:
                lines.append(f"  Items: {', '.join(valid_items)}")

        return lines
