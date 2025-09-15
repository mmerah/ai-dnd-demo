"""Handler for dice-related commands."""

import logging

from app.agents.core.types import AgentType
from app.events.base import BaseCommand, CommandResult
from app.events.commands.dice_commands import RollDiceCommand
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.common import IDiceService
from app.models.game_state import GameState
from app.models.tool_results import RollDiceResult

logger = logging.getLogger(__name__)


class DiceHandler(BaseHandler):
    """Handler for dice-related commands."""

    def __init__(self, dice_service: IDiceService) -> None:
        self.dice_service = dice_service

    supported_commands = (RollDiceCommand,)

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle dice commands."""
        result = CommandResult()

        if isinstance(command, RollDiceCommand):
            # Validate agent type during combat
            # During combat, only combat agent should roll combat-related dice
            if (
                game_state.combat.is_active
                and command.roll_type in ("attack", "damage", "initiative")
                and command.agent_type
                and command.agent_type != AgentType.COMBAT
            ):
                logger.warning(
                    f"Combat roll ({command.roll_type}) made by {command.agent_type.value} agent during active combat - should be COMBAT agent only"
                )
            # Parse special dice notations for advantage/disadvantage
            dice_str, roll_type = self.dice_service.parse_special_notation(command.dice)

            # Construct dice formula with modifier
            if command.modifier > 0:
                formula = f"{dice_str}+{command.modifier}"
            elif command.modifier < 0:
                formula = f"{dice_str}{command.modifier}"
            else:
                formula = dice_str

            # Perform the dice roll
            roll_result = self.dice_service.roll_dice(formula, roll_type)

            # Create the result model
            dice_result = RollDiceResult(
                type=f"dice_roll_{command.roll_type}",
                roll_type=command.roll_type,
                dice=command.dice,
                modifier=command.modifier,
                rolls=roll_result.rolls,
                total=roll_result.total,
                ability=command.ability,
                skill=command.skill,
                critical=roll_result.is_critical_failure or roll_result.is_critical_success,
            )
            result.data = dice_result

            logger.debug(
                f"Dice Roll: {command.roll_type} - {formula} = {roll_result.total} (rolls: {roll_result.rolls})",
            )

        return result
