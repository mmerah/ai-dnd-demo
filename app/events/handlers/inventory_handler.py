"""Handler for inventory-related commands."""

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.inventory_commands import (
    EquipItemCommand,
    ModifyCurrencyCommand,
    ModifyInventoryCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.character import ICharacterService, IEntityStateService
from app.interfaces.services.data import IRepositoryProvider
from app.models.equipment_slots import EquipmentSlotType
from app.models.game_state import GameState
from app.models.item import InventoryItem
from app.models.tool_results import (
    AddItemResult,
    EquipItemResult,
    ModifyCurrencyResult,
    RemoveItemResult,
)

logger = logging.getLogger(__name__)


class InventoryHandler(BaseHandler):
    """Handler for inventory-related commands."""

    def __init__(
        self,
        character_service: ICharacterService,
        entity_state_service: IEntityStateService,
        repository_provider: IRepositoryProvider,
    ):
        self.character_service = character_service
        self.entity_state_service = entity_state_service
        self.repository_provider = repository_provider

    supported_commands = (
        ModifyCurrencyCommand,
        ModifyInventoryCommand,
        EquipItemCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle inventory commands."""
        result = CommandResult()
        character = game_state.character.state

        if isinstance(command, ModifyCurrencyCommand):
            # Modify currency for the player
            old_currency, new_currency = self.entity_state_service.modify_currency(
                game_state,
                entity_id=game_state.character.instance_id,
                gold=command.gold,
                silver=command.silver,
                copper=command.copper,
            )

            # Mark mutated if any currency value changed
            result.mutated = (
                old_currency.gold != new_currency.gold
                or old_currency.silver != new_currency.silver
                or old_currency.copper != new_currency.copper
            )

            result.data = ModifyCurrencyResult(
                old_gold=old_currency.gold,
                old_silver=old_currency.silver,
                old_copper=old_currency.copper,
                new_gold=new_currency.gold,
                new_silver=new_currency.silver,
                new_copper=new_currency.copper,
                change_gold=command.gold,
                change_silver=command.silver,
                change_copper=command.copper,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(
                f"Currency Update: Gold {old_currency.gold}→{new_currency.gold}, "
                f"Silver {old_currency.silver}→{new_currency.silver}, "
                f"Copper {old_currency.copper}→{new_currency.copper}",
            )

        elif isinstance(command, ModifyInventoryCommand) and command.quantity > 0:
            # Check if item already exists in inventory
            existing_item = next((item for item in character.inventory if item.index == command.item_index), None)

            if existing_item:
                existing_item.quantity += command.quantity
            else:
                # Try to get item from repository, or create placeholder if it doesn't exist
                item_repo = self.repository_provider.get_item_repository_for(game_state)
                if not item_repo.validate_reference(command.item_index):
                    # Create a placeholder item for dynamic items not in the repository
                    logger.warning(f"Creating placeholder item for AI-invented item: '{command.item_index}'")
                    # TODO(MVP2): Implement dynamic item creation tool for AI to define custom items
                    # TODO(MVP2): Should already be put in some kind of ISandbox or ICreator interface
                    new_item = self.character_service.create_placeholder_item(
                        game_state, command.item_index, command.quantity
                    )
                    character.inventory.append(new_item)
                else:
                    # Get item definition from repository
                    try:
                        item_def = item_repo.get(command.item_index)
                        new_item = InventoryItem.from_definition(item_def, quantity=command.quantity)
                        character.inventory.append(new_item)
                    except RepositoryNotFoundError as e:
                        raise ValueError(f"Failed to load item definition: {command.item_index}") from e

            result.mutated = True

            result.data = AddItemResult(
                item_index=command.item_index,
                quantity=command.quantity,
                total_quantity=existing_item.quantity if existing_item else command.quantity,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Item Added: {command.item_index} x{command.quantity}")

        elif isinstance(command, ModifyInventoryCommand) and command.quantity <= 0:
            existing_item = next((item for item in character.inventory if item.index == command.item_index), None)

            if not existing_item:
                raise ValueError(f"Item {command.item_index} not found in inventory")

            # Check if item is equipped and prevent removal if so
            equipped_slots = character.equipment_slots.find_item_slots(command.item_index)
            equipped_count = len(equipped_slots)
            removable = existing_item.quantity - equipped_count
            need = abs(command.quantity)
            if removable < need:
                raise ValueError(
                    f"Not enough unequipped {existing_item.index} to remove (have {removable}, need {need}). Unequip first."
                )

            existing_item.quantity -= need

            # Remove item completely if quantity reaches 0
            if existing_item.quantity == 0:
                character.inventory.remove(existing_item)

            result.mutated = True

            result.data = RemoveItemResult(
                item_index=command.item_index,
                quantity=command.quantity,
                remaining_quantity=max(0, existing_item.quantity),
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Item Removed: {command.item_index} x{command.quantity}")

        elif isinstance(command, EquipItemCommand):
            # Convert string slot to enum if provided
            slot_type = None
            if command.slot:
                try:
                    slot_type = EquipmentSlotType(command.slot)
                except ValueError as exc:
                    raise ValueError(f"Invalid equipment slot: {command.slot}") from exc

            self.entity_state_service.equip_item(
                game_state, game_state.character.instance_id, command.item_index, slot_type, command.unequip
            )

            result.mutated = True
            result.recompute_state = True

            # Determine action message
            if command.unequip:
                message = f"Unequipped {command.item_index}"
            elif command.slot:
                message = f"Equipped {command.item_index} in {command.slot}"
            else:
                message = f"Equipped {command.item_index}"

            result.data = EquipItemResult(
                item_index=command.item_index,
                equipped=not command.unequip,
                slot=command.slot,
                message=message,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(message)

        return result
