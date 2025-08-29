"""Handler for dice-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastToolResultCommand
from app.events.commands.dice_commands import RollDiceCommand
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services import IGameService
from app.models.game_state import GameState
from app.services.dice_service import DiceService

logger = logging.getLogger(__name__)


class DiceHandler(BaseHandler):
    """Handler for dice-related commands."""

    def __init__(self, game_service: IGameService, dice_service: DiceService) -> None:
        super().__init__(game_service)
        self.dice_service = dice_service

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle dice commands."""
        result = CommandResult(success=True)

        if isinstance(command, RollDiceCommand):
            from app.services.dice_service import RollType

            # Parse special dice notations for advantage/disadvantage
            dice_str = command.dice
            roll_type = RollType.NORMAL

            if dice_str == "2d20kh":  # Keep highest (advantage)
                dice_str = "1d20"
                roll_type = RollType.ADVANTAGE
            elif dice_str == "2d20kl":  # Keep lowest (disadvantage)
                dice_str = "1d20"
                roll_type = RollType.DISADVANTAGE

            # Construct dice formula with modifier
            if command.modifier > 0:
                formula = f"{dice_str}+{command.modifier}"
            elif command.modifier < 0:
                formula = f"{dice_str}{command.modifier}"
            else:
                formula = dice_str

            # Perform the dice roll
            roll_result = self.dice_service.roll_dice(formula, roll_type)

            result.data = {
                "type": f"dice_roll_{command.roll_type}",
                "roll_type": command.roll_type,
                "dice": command.dice,
                "modifier": command.modifier,
                "rolls": roll_result.rolls,
                "total": roll_result.total,
                "target": command.target,
                "ability": command.ability,
                "skill": command.skill,
                "damage_type": command.damage_type,
            }

            # Create broadcast command for the result
            result.add_command(
                BroadcastToolResultCommand(
                    game_id=command.game_id, tool_name=f"roll_{command.roll_type}", result=result.data
                )
            )

            logger.info(
                f"Dice Roll: {command.roll_type} - {formula} = {roll_result.total} " f"(rolls: {roll_result.rolls})"
            )

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, RollDiceCommand)
