"""Handler for inventory-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastCharacterUpdateCommand
from app.events.commands.inventory_commands import (
    AddItemCommand,
    ModifyCurrencyCommand,
    RemoveItemCommand,
)
from app.events.handlers.base_handler import BaseHandler
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

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle inventory commands."""
        result = CommandResult(success=True)
        character = game_state.character

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

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(
                f"Currency Update: Gold {old_gold}→{character.currency.gold}, "
                f"Silver {old_silver}→{character.currency.silver}, "
                f"Copper {old_copper}→{character.currency.copper}",
            )

        elif isinstance(command, AddItemCommand):
            # Check if item already exists in inventory
            existing_item = next((item for item in character.inventory if item.name == command.item_name), None)

            if existing_item:
                existing_item.quantity += command.quantity
            else:
                new_item = InventoryItem(
                    name=command.item_name,
                    quantity=command.quantity,
                    weight=0.0,  # Would need item database for accurate weight
                    value=0.0,  # Would need item database for accurate value
                )
                character.inventory.append(new_item)

            self.game_service.save_game(game_state)

            result.data = AddItemResult(
                item_name=command.item_name,
                quantity=command.quantity,
                total_quantity=existing_item.quantity if existing_item else command.quantity,
            )

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(f"Item Added: {command.item_name} x{command.quantity}")

        elif isinstance(command, RemoveItemCommand):
            existing_item = next((item for item in character.inventory if item.name == command.item_name), None)

            if not existing_item:
                result.success = False
                result.error = f"Item {command.item_name} not found in inventory"
                return result

            if existing_item.quantity < command.quantity:
                result.success = False
                result.error = (
                    f"Not enough {command.item_name} (have {existing_item.quantity}, need {command.quantity})"
                )
                return result

            existing_item.quantity -= command.quantity

            # Remove item completely if quantity reaches 0
            if existing_item.quantity == 0:
                character.inventory.remove(existing_item)

            self.game_service.save_game(game_state)

            result.data = RemoveItemResult(
                item_name=command.item_name,
                quantity=command.quantity,
                remaining_quantity=max(0, existing_item.quantity),
            )

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(f"Item Removed: {command.item_name} x{command.quantity}")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, ModifyCurrencyCommand | AddItemCommand | RemoveItemCommand)
