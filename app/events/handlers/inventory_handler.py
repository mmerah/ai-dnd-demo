"""Handler for inventory-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.inventory_commands import (
    ModifyCurrencyCommand,
    ModifyInventoryCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.data import IItemRepository
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState
from app.models.item import InventoryItem
from app.models.tool_results import (
    AddItemResult,
    ModifyCurrencyResult,
    RemoveItemResult,
)

logger = logging.getLogger(__name__)


class InventoryHandler(BaseHandler):
    """Handler for inventory-related commands."""

    def __init__(self, game_service: IGameService, item_repository: IItemRepository):
        super().__init__(game_service)
        self.item_repository = item_repository

    supported_commands = (
        ModifyCurrencyCommand,
        ModifyInventoryCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle inventory commands."""
        result = CommandResult()
        character = game_state.character.state

        if isinstance(command, ModifyCurrencyCommand):
            old_gold = character.currency.gold
            old_silver = character.currency.silver
            old_copper = character.currency.copper

            character.currency.gold += command.gold
            character.currency.silver += command.silver
            character.currency.copper += command.copper

            # Handle negative values
            character.currency.gold = max(character.currency.gold, 0)
            character.currency.silver = max(character.currency.silver, 0)
            character.currency.copper = max(character.currency.copper, 0)

            self.game_service.save_game(game_state)

            result.data = ModifyCurrencyResult(
                old_gold=old_gold,
                old_silver=old_silver,
                old_copper=old_copper,
                new_gold=character.currency.gold,
                new_silver=character.currency.silver,
                new_copper=character.currency.copper,
                change_gold=command.gold,
                change_silver=command.silver,
                change_copper=command.copper,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(
                f"Currency Update: Gold {old_gold}→{character.currency.gold}, "
                f"Silver {old_silver}→{character.currency.silver}, "
                f"Copper {old_copper}→{character.currency.copper}",
            )

        elif isinstance(command, ModifyInventoryCommand) and command.quantity > 0:
            # Check if item already exists in inventory
            existing_item = next((item for item in character.inventory if item.name == command.item_name), None)

            if existing_item:
                existing_item.quantity += command.quantity
            else:
                # Validate item exists in repository (fail-fast)
                if not self.item_repository.validate_reference(command.item_name):
                    raise ValueError(f"Unknown item: {command.item_name}")

                # Get item definition and create properly
                item_def = self.item_repository.get(command.item_name)
                if not item_def:
                    raise ValueError(f"Failed to load item definition: {command.item_name}")

                new_item = InventoryItem.from_definition(item_def, quantity=command.quantity, equipped_quantity=0)
                character.inventory.append(new_item)

            self.game_service.save_game(game_state)

            result.data = AddItemResult(
                item_name=command.item_name,
                quantity=command.quantity,
                total_quantity=existing_item.quantity if existing_item else command.quantity,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Item Added: {command.item_name} x{command.quantity}")

        elif isinstance(command, ModifyInventoryCommand) and command.quantity <= 0:
            existing_item = next((item for item in character.inventory if item.name == command.item_name), None)

            if not existing_item:
                raise ValueError(f"Item {command.item_name} not found in inventory")

            # Do not allow removing equipped units implicitly
            removable = (existing_item.quantity or 0) - (existing_item.equipped_quantity or 0)
            need = abs(command.quantity)
            if removable < need:
                raise ValueError(
                    f"Not enough unequipped {command.item_name} to remove (have {removable}, need {need}). Unequip first."
                )

            existing_item.quantity -= need

            # Remove item completely if quantity reaches 0
            if existing_item.quantity == 0:
                character.inventory.remove(existing_item)

            self.game_service.save_game(game_state)

            result.data = RemoveItemResult(
                item_name=command.item_name,
                quantity=command.quantity,
                remaining_quantity=max(0, existing_item.quantity),
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Item Removed: {command.item_name} x{command.quantity}")

        return result
