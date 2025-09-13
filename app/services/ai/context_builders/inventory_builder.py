from app.models.game_state import GameState

from .base import ContextBuilder


class InventoryContextBuilder(ContextBuilder):
    """List player's inventory with exact item names and quantities."""

    def build(self, game_state: GameState) -> str | None:
        inv = game_state.character.state.inventory
        if not inv:
            return None

        lines = ["Your Inventory (use exact indexes):"]
        for item in inv[:20]:
            lines.append(f"  - {item.index} x{item.quantity}")
        return "\n".join(lines)
