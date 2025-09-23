"""Unit tests for ItemManagerService service."""

from unittest.mock import create_autospec

from app.interfaces.services.data import IRepository, IRepositoryProvider
from app.models.item import ItemDefinition, ItemRarity, ItemType
from app.services.game.item_manager_service import ItemManagerService
from tests.factories import make_game_state


class TestItemManagerService:
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository_provider = create_autospec(IRepositoryProvider, instance=True)
        self.item_repository = create_autospec(IRepository, instance=True)
        self.repository_provider.get_item_repository_for.return_value = self.item_repository

        self.item_manager_service = ItemManagerService(repository_provider=self.repository_provider)
        self.game_state = make_game_state()

    def test_create_item_from_repository(self) -> None:
        """Test creating an item that exists in the repository."""
        item_def = ItemDefinition(
            index="longsword",
            name="Longsword",
            type=ItemType.WEAPON,
            rarity=ItemRarity.COMMON,
            description="A longsword",
            weight=3.0,
            value=15,
            content_pack="core",
        )
        self.item_repository.validate_reference.return_value = True
        self.item_repository.get.return_value = item_def

        result = self.item_manager_service.create_inventory_item(self.game_state, "longsword", quantity=2)

        assert result.index == "longsword"
        assert result.quantity == 2

    def test_create_placeholder_for_unknown_item(self) -> None:
        """Test creating a placeholder when item doesn't exist."""
        self.item_repository.validate_reference.return_value = False

        result = self.item_manager_service.create_inventory_item(self.game_state, "mystery-token", quantity=1)

        assert result.index == "mystery-token"
        assert result.name == "Mystery Token"
        # Default type
        assert result.item_type == ItemType.ADVENTURING_GEAR
