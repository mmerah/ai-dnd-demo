"""Helper functions for executing player-initiated actions with proper event tracking."""

import logging
from typing import TypeVar

from pydantic import BaseModel

from app.events.base import BaseCommand
from app.interfaces.services.common import IActionService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def execute_player_action(
    command: BaseCommand,
    tool_name: str,
    game_state: GameState,
    action_service: IActionService,
) -> T:
    """Execute a player-initiated command with proper event tracking.

    This mirrors what @tool_handler does for AI tools, ensuring that player
    actions are tracked in game events just like AI tool calls.

    Args:
        command: The command to execute
        tool_name: Name of the "tool" (action) for event tracking
        game_state: Current game state
        action_service: Service that executes actions with broadcasting/persistence

    Returns:
        The result from command execution

    Raises:
        ValueError: If command execution fails or returns invalid result
    """
    result = await action_service.execute_command_as_action(tool_name=tool_name, command=command, game_state=game_state)
    return result  # type: ignore[return-value]
