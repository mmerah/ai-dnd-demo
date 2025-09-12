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
from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.data import IItemRepository
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState
from app.models.item import InventoryItem, ItemDefinition, ItemRarity, ItemType
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
        self, game_service: IGameService, item_repository: IItemRepository, compute_service: ICharacterComputeService
    ):
        super().__init__(game_service)
        self.item_repository = item_repository
        self.compute_service = compute_service

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

            # Mark mutated if any currency value changed
            result.mutated = (
                character.currency.gold != old_gold
                or character.currency.silver != old_silver
                or character.currency.copper != old_copper
            )

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
                # Try to get item from repository, or create placeholder if it doesn't exist
                if not self.item_repository.validate_reference(command.item_name):
                    # Create a placeholder item for dynamic items not in the repository
                    logger.warning(f"Creating placeholder item for unknown item: '{command.item_name}'")
                    # TODO: Implement dynamic item creation tool for AI to define custom items
                    item_def = ItemDefinition(
                        name=command.item_name,
                        type=ItemType.ADVENTURING_GEAR,
                        rarity=ItemRarity.COMMON,
                        description=f"A unique item: {command.item_name}",
                        weight=0.5,
                        value=1,
                    )
                    new_item = InventoryItem.from_definition(item_def, quantity=command.quantity, equipped_quantity=0)
                    character.inventory.append(new_item)
                else:
                    # Get item definition from repository
                    try:
                        item_def = self.item_repository.get(command.item_name)
                        new_item = InventoryItem.from_definition(
                            item_def, quantity=command.quantity, equipped_quantity=0
                        )
                        character.inventory.append(new_item)
                    except RepositoryNotFoundError as e:
                        raise ValueError(f"Failed to load item definition: {command.item_name}") from e

            result.mutated = True

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

            result.mutated = True

            result.data = RemoveItemResult(
                item_name=command.item_name,
                quantity=command.quantity,
                remaining_quantity=max(0, existing_item.quantity),
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Item Removed: {command.item_name} x{command.quantity}")

        elif isinstance(command, EquipItemCommand):
            try:
                game_state.character.state = self.compute_service.set_item_equipped(
                    game_state.character.state, command.item_name, command.equipped
                )

                # Find the item to get equipped quantity
                item = next(
                    (it for it in game_state.character.state.inventory if it.name.lower() == command.item_name.lower()),
                    None,
                )
                equipped_qty = item.equipped_quantity if item else 0

                # Recompute derived values
                self.game_service.recompute_character_state(game_state)
                result.mutated = True

                result.data = EquipItemResult(
                    item_name=item.name if item else command.item_name,
                    equipped=command.equipped,
                    equipped_quantity=equipped_qty,
                    message=f"{'Equipped' if command.equipped else 'Unequipped'} {command.item_name}",
                )

                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
                logger.info(f"Item {'Equipped' if command.equipped else 'Unequipped'}: {command.item_name}")

            except ValueError as e:
                raise ValueError(f"Failed to equip/unequip item: {e}") from e

        return result
