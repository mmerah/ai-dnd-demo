"""Item factory service implementation."""

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game.item_factory import IItemFactory
from app.models.game_state import GameState
from app.models.item import InventoryItem, ItemDefinition, ItemRarity, ItemType

logger = logging.getLogger(__name__)


class ItemFactory(IItemFactory):
    """Factory for creating inventory items with placeholder support."""

    def __init__(self, repository_provider: IRepositoryProvider):
        """Initialize the item factory.

        Args:
            repository_provider: Provider for accessing item repositories
        """
        self.repository_provider = repository_provider

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
        """
        item_repo = self.repository_provider.get_item_repository_for(game_state)

        # Validation stays in repository
        if item_repo.validate_reference(item_index):
            try:
                item_def = item_repo.get(item_index)
                return InventoryItem.from_definition(item_def, quantity=quantity)
            except RepositoryNotFoundError as e:
                # TODO(MVP2): Implement dynamic item creation tool for AI to define custom items
                # Shouldn't happen if validate_reference returned True, but handle gracefully
                logger.error(f"Item {item_index} validated but not found: {e}")
                return self._create_placeholder(item_index, quantity)
        else:
            # Create placeholder for AI-invented items
            logger.warning(f"Creating placeholder for dynamic item: {item_index}")
            return self._create_placeholder(item_index, quantity)

    def _create_placeholder(self, item_index: str, quantity: int) -> InventoryItem:
        """Create a placeholder item for unknown item indices.

        This supports AI-generated items that don't exist in the repository.

        Args:
            item_index: Item index that doesn't exist in repository
            quantity: Number of items

        Returns:
            Placeholder InventoryItem
        """
        # Use index as name for placeholder items
        item_name = item_index.replace("-", " ").title()
        item_def = ItemDefinition(
            index=item_index,
            name=item_name,
            type=ItemType.ADVENTURING_GEAR,
            rarity=ItemRarity.COMMON,
            description=f"A unique item: {item_name}",
            weight=0.5,
            value=1,
            content_pack="sandbox",
        )
        return InventoryItem.from_definition(item_def, quantity=quantity)
