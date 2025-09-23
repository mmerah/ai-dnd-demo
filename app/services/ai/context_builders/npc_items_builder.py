from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class NPCItemsContextBuilder(ContextBuilder):
    """Build context about items NPCs have available for trade/giving."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
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
                if item.index not in items_mentioned:
                    items_mentioned.add(item.index)
                    if context.item_repository.validate_reference(item.index):
                        npc_items.append(f"{item.index}")

            if npc_items:
                if not context_parts:
                    context_parts.append("NPC Available Items (use exact index shown):")
                context_parts.append(f"  {npc.sheet.character.name} has: {', '.join(npc_items)}")

        return "\n".join(context_parts) if context_parts else None
