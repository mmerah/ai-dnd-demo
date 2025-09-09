"""Helper functions for executing player-initiated actions with proper event tracking."""

import logging
from typing import TypeVar

from pydantic import BaseModel

from app.events.base import BaseCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.game import IEventManager, ISaveManager
from app.models.game_state import GameEventType, GameState
from app.models.tool_results import ToolResult

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


async def execute_player_action(
    command: BaseCommand,
    tool_name: str,
    game_state: GameState,
    event_bus: IEventBus,
    event_manager: IEventManager,
    save_manager: ISaveManager,
) -> T:
    """Execute a player-initiated command with proper event tracking.

    This mirrors what @tool_handler does for AI tools, ensuring that player
    actions are tracked in game events just like AI tool calls.

    Args:
        command: The command to execute
        tool_name: Name of the "tool" (action) for event tracking
        game_state: Current game state
        event_bus: Event bus for command execution
        event_manager: Manager for game events
        save_manager: Manager for saving game state

    Returns:
        The result from command execution

    Raises:
        ValueError: If command execution fails or returns invalid result
    """
    # 1. Persist TOOL_CALL event (treating player actions as "player tools")
    parameters = {k: v for k, v in command.__dict__.items() if k not in ("game_id", "priority", "timestamp")}

    try:
        event_manager.add_event(
            game_state=game_state,
            event_type=GameEventType.TOOL_CALL,
            tool_name=tool_name,
            parameters=parameters,
        )
        save_manager.save_game(game_state)
    except Exception as e:
        # Log but don't fail the action if event persistence fails
        logger.error(
            f"Failed to persist TOOL_CALL for player action {tool_name}: {e}",
            exc_info=True,
        )

    # 2. Execute the command
    result = await event_bus.execute_command(command)

    if not result:
        raise ValueError(f"Command {type(command).__name__} returned None for {tool_name}")

    # 3. Persist TOOL_RESULT event if result is a ToolResult
    if isinstance(result, ToolResult):
        try:
            event_manager.add_event(
                game_state=game_state,
                event_type=GameEventType.TOOL_RESULT,
                tool_name=tool_name,
                result=result.model_dump(mode="json"),
            )
            save_manager.save_game(game_state)
        except Exception as e:
            logger.error(
                f"Failed to persist TOOL_RESULT for player action {tool_name}: {e}",
                exc_info=True,
            )

    return result  # type: ignore[return-value]
