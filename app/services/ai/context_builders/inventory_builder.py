from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, EntityContextBuilder


class InventoryContextBuilder(EntityContextBuilder):
    """List entity's inventory with exact item names and quantities.

    Builds inventory context for any entity (player or NPC).
    """

    MAX_INVENTORY_ITEMS = 20

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # Extract entity name based on type
        entity_name = f"{entity.display_name}'s" if isinstance(entity, NPCInstance) else "Player's"

        inv = entity.state.inventory
        if not inv:
            return None

        lines = [f"{entity_name} Inventory (use exact indexes):"]
        for item in inv[: self.MAX_INVENTORY_ITEMS]:
            lines.append(f"  - {item.index} x{item.quantity}")
        return "\n".join(lines)
