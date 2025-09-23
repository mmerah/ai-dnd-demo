from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class NPCsAtLocationContextBuilder(ContextBuilder):
    """Build context for NPCs present at the current location."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
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
