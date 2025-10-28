from unittest.mock import create_autospec

import pytest

from app.events.commands.inventory_commands import EquipItemCommand, ModifyCurrencyCommand, ModifyInventoryCommand
from app.events.handlers.inventory_handler import InventoryHandler
from app.interfaces.services.character import IEntityStateService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import IItemManagerService
from app.models.attributes import EntityType
from app.models.character import Currency
from app.models.equipment_slots import EquipmentSlotType
from app.models.item import InventoryItem
from app.models.tool_results import AddItemResult, RemoveItemResult
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class TestInventoryHandler:
    def setup_method(self) -> None:
        self.item_manager_service = create_autospec(IItemManagerService, instance=True)
        self.entity_state_service = create_autospec(IEntityStateService, instance=True)
        self.repository_provider = create_autospec(IRepositoryProvider, instance=True)
        self.handler = InventoryHandler(self.item_manager_service, self.entity_state_service, self.repository_provider)
        self.game_state = make_game_state()
        self.character_state = self.game_state.character.state
        self.player_id = self.game_state.character.instance_id

    @pytest.mark.asyncio
    async def test_add_placeholder_item(self) -> None:
        gs = self.game_state
        placeholder = InventoryItem(index="mystery-token", name="Mystery Token", quantity=2)
        self.item_manager_service.create_inventory_item.return_value = placeholder

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
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
            entity_id=self.player_id,
            entity_type=EntityType.PLAYER,
            item_index="nonexistent",
            quantity=-1,
        )

        with pytest.raises(ValueError, match="Item .* not found in inventory"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_add_item_to_npc_inventory(self) -> None:
        """Test that NPCs can have items added to their inventory."""
        gs = self.game_state

        # Create an NPC and add to game state
        npc_sheet = make_npc_sheet(npc_id="companion")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="companion-inst")
        gs.npcs.append(npc)
        gs.party.add_member(npc.instance_id)

        # Create item to add
        item = InventoryItem(index="healing-potion", name="Healing Potion", quantity=1)
        self.item_manager_service.create_inventory_item.return_value = item

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            item_index=item.index,
            quantity=1,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AddItemResult)
        assert result.data.item_index == item.index
        assert result.mutated
        assert npc.state.inventory[0].index == item.index

    @pytest.mark.asyncio
    async def test_modify_currency_for_npc(self) -> None:
        """Test that NPCs can have their currency modified."""
        gs = self.game_state

        # Create an NPC and add to game state
        npc_sheet = make_npc_sheet(npc_id="merchant")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="merchant-inst")
        gs.npcs.append(npc)
        gs.party.add_member(npc.instance_id)

        # Mock entity state service to update currency
        self.entity_state_service.modify_currency.return_value = (
            Currency(gold=0, silver=0, copper=0),
            Currency(gold=10, silver=5, copper=0),
        )

        command = ModifyCurrencyCommand(
            game_id=gs.game_id,
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            gold=10,
            silver=5,
        )
        result = await self.handler.handle(command, gs)

        assert result.mutated
        self.entity_state_service.modify_currency.assert_called_once_with(
            gs, npc.instance_id, gold=10, silver=5, copper=0
        )

    @pytest.mark.asyncio
    async def test_equip_item_for_npc(self) -> None:
        """Test that NPCs can equip items."""
        gs = self.game_state

        # Create an NPC and add to game state
        npc_sheet = make_npc_sheet(npc_id="warrior")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="warrior-inst")
        gs.npcs.append(npc)
        gs.party.add_member(npc.instance_id)

        # Add item to NPC inventory
        item = InventoryItem(index="shield", name="Shield", quantity=1)
        npc.state.inventory.append(item)

        command = EquipItemCommand(
            game_id=gs.game_id,
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            item_index=item.index,
            slot="off_hand",
            unequip=False,
        )
        result = await self.handler.handle(command, gs)

        assert result.mutated
        self.entity_state_service.equip_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_cannot_modify_inventory_for_monster(self) -> None:
        """Test that inventory operations are rejected for monsters."""
        gs = self.game_state

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id="goblin-1",
            entity_type=EntityType.MONSTER,
            item_index="sword",
            quantity=1,
        )

        with pytest.raises(ValueError, match="Inventory operations are not supported for monsters"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_cannot_modify_inventory_for_nonexistent_entity(self) -> None:
        """Test that operations fail gracefully for nonexistent entities."""
        gs = self.game_state

        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id="nonexistent-npc",
            entity_type=EntityType.NPC,
            item_index="sword",
            quantity=1,
        )

        with pytest.raises(ValueError, match="Entity with ID .* not found"):
            await self.handler.handle(command, gs)

    @pytest.mark.asyncio
    async def test_player_shorthand_for_modify_inventory(self) -> None:
        """Test that entity_id='player' works as shorthand for player character."""
        gs = self.game_state
        placeholder = InventoryItem(index="magic-item", name="Magic Item", quantity=1)
        self.item_manager_service.create_inventory_item.return_value = placeholder

        # Use "player" as entity_id instead of actual instance_id
        command = ModifyInventoryCommand(
            game_id=gs.game_id,
            entity_id="player",
            entity_type=EntityType.PLAYER,
            item_index=placeholder.index,
            quantity=1,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AddItemResult)
        assert result.data.item_index == placeholder.index
        assert result.mutated
        assert self.character_state.inventory[0].index == placeholder.index
