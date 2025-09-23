from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class NPCDetailContextBuilder(ContextBuilder):
    """Build detailed NPC context with abilities for NPCs at the current location."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
        npcs_here = [npc for npc in game_state.npcs if npc.current_location_id == current_loc_id]
        if not npcs_here:
            return None

        npc_lines = ["NPCs Present (Detailed):"]
        for npc in npcs_here:
            npc_name = npc.sheet.character.name
            npc_state = npc.state
            npc_info = (
                f"  • {npc_name} [ID: {npc.instance_id}]: "
                f"HP {npc_state.hit_points.current}/{npc_state.hit_points.maximum}, AC {npc_state.armor_class}"
            )
            if npc_state.conditions:
                npc_info += f" [{', '.join(npc_state.conditions)}]"
            npc_lines.append(npc_info)
            ability_summary = f"    Abilities - STR: {npc_state.abilities.STR}, DEX: {npc_state.abilities.DEX}, CON: {npc_state.abilities.CON}"
            npc_lines.append(ability_summary)

        return "\n".join(npc_lines)
