from unittest.mock import MagicMock, create_autospec

import pytest

from app.events.commands.inventory_commands import ModifyInventoryCommand
from app.events.handlers.inventory_handler import InventoryHandler
from app.interfaces.services.character import ICharacterService, IEntityStateService
from app.interfaces.services.data import IRepositoryProvider
from app.models.equipment_slots import EquipmentSlotType
from app.models.item import InventoryItem
from app.models.tool_results import AddItemResult, RemoveItemResult
from tests.factories import make_game_state


class TestInventoryHandler:
    def setup_method(self) -> None:
        self.character_service = create_autospec(ICharacterService, instance=True)
        self.entity_state_service = create_autospec(IEntityStateService, instance=True)
        self.repository_provider = create_autospec(IRepositoryProvider, instance=True)
        self.handler = InventoryHandler(self.character_service, self.entity_state_service, self.repository_provider)
        self.game_state = make_game_state()
        self.character_state = self.game_state.character.state

    @pytest.mark.asyncio
    async def test_add_placeholder_item(self) -> None:
        gs = self.game_state
        placeholder = InventoryItem(index="mystery-token", name="Mystery Token", quantity=2)

        repo = MagicMock()
        repo.validate_reference.return_value = False
        self.repository_provider.get_item_repository_for.return_value = repo
        self.character_service.create_placeholder_item.return_value = placeholder

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index=placeholder.index,
            quantity=2,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AddItemResult)
        assert result.data.item_index == placeholder.index
        assert result.data.quantity == 2
        assert self.character_state.inventory[0].index == placeholder.index
        assert result.mutated
        assert len(result.follow_up_commands) > 0

    @pytest.mark.asyncio
    async def test_add_existing_item_increases_quantity(self) -> None:
        gs = self.game_state
        existing_item = InventoryItem(index="torch", name="Torch", quantity=3)
        self.character_state.inventory.append(existing_item)

        repo = MagicMock()
        repo.validate_reference.return_value = True
        self.repository_provider.get_item_repository_for.return_value = repo

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index="torch",
            quantity=2,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AddItemResult)
        assert result.data.total_quantity == 5
        assert self.character_state.inventory[0].quantity == 5

    @pytest.mark.asyncio
    async def test_remove_item(self) -> None:
        gs = self.game_state
        item = InventoryItem(index="torch", name="Torch", quantity=5)
        self.character_state.inventory.append(item)

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index="torch",
            quantity=-2,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, RemoveItemResult)
        assert result.data.quantity == -2
        assert result.data.remaining_quantity == 3
        assert self.character_state.inventory[0].quantity == 3

    @pytest.mark.asyncio
    async def test_remove_all_items(self) -> None:
        gs = self.game_state
        item = InventoryItem(index="torch", name="Torch", quantity=2)
        self.character_state.inventory.append(item)

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index="torch",
            quantity=-2,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, RemoveItemResult)
        assert result.data.remaining_quantity == 0
        assert len(self.character_state.inventory) == 0

    @pytest.mark.asyncio
    async def test_cannot_remove_equipped_item(self) -> None:
        gs = self.game_state
        item = InventoryItem(index="longsword", quantity=1)
        self.character_state.inventory.append(item)
        self.character_state.equipment_slots.set_slot(EquipmentSlotType.MAIN_HAND, item.index)

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index=item.index,
            quantity=-1,
        )

        with pytest.raises(ValueError, match="Unequip first"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_cannot_remove_more_than_available(self) -> None:
        gs = self.game_state
        item = InventoryItem(index="torch", name="Torch", quantity=2)
        self.character_state.inventory.append(item)

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index="torch",
            quantity=-5,
        )

        with pytest.raises(ValueError, match="Not enough unequipped"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_cannot_remove_nonexistent_item(self) -> None:
        gs = self.game_state

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            item_index="nonexistent",
            quantity=-1,
        )

        with pytest.raises(ValueError, match="Item .* not found in inventory"):
            await self.handler.handle(command, gs)
