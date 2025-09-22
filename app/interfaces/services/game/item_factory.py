"""Interface for item factory service."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.item import InventoryItem


class IItemFactory(ABC):
    """Factory for creating inventory items with placeholder support."""

    @abstractmethod
    def create_inventory_item(
        self,
        game_state: GameState,
        item_index: str,
        quantity: int = 1,
    ) -> InventoryItem:
        """Create or retrieve an inventory item, with placeholder support.

        Args:
            game_state: Current game state for repository access
            item_index: Item index to create
            quantity: Number of items to create

        Returns:
            InventoryItem instance, either from repository or as placeholder

        Raises:
            ValueError: If item creation fails
        """
        pass
