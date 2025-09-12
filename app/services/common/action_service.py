"""Common service to execute game actions (AI or player) with unified tracking.

Centralizes the sequence:
- Broadcast tool call
- Persist TOOL_CALL event
- Execute command
- Broadcast tool result (if ToolResult)
- Persist TOOL_RESULT event (if ToolResult)
"""

import logging

from pydantic import BaseModel

from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.events.commands.broadcast_commands import (
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.interfaces.events import IEventBus
from app.interfaces.services.common import IActionService
from app.interfaces.services.game import IEventManager, ISaveManager
from app.models.game_state import GameEventType, GameState
from app.models.tool_results import ToolResult

logger = logging.getLogger(__name__)


class ActionService(IActionService):
    """Execute commands as actions with consistent broadcasting and persistence."""

    def __init__(self, event_bus: IEventBus, event_manager: IEventManager, save_manager: ISaveManager) -> None:
        self.event_bus = event_bus
        self.event_manager = event_manager
        self.save_manager = save_manager

    async def execute_command_as_action(
        self,
        tool_name: str,
        command: BaseCommand,
        game_state: GameState,
        broadcast_parameters: dict[str, JSONSerializable] | None = None,
    ) -> BaseModel:
        # Extract parameters from command for persistence/broadcast if not provided
        if broadcast_parameters is None:
            broadcast_parameters = {
                k: v for k, v in command.__dict__.items() if k not in ("game_id", "priority", "timestamp")
            }

        # 1) Broadcast tool call
        await self.event_bus.submit_command(
            BroadcastToolCallCommand(
                game_id=game_state.game_id,
                tool_name=tool_name,
                parameters=broadcast_parameters,
            ),
        )

        # 2) Persist TOOL_CALL
        try:
            self.event_manager.add_event(
                game_state=game_state,
                event_type=GameEventType.TOOL_CALL,
                tool_name=tool_name,
                parameters=broadcast_parameters,
            )
            self.save_manager.save_game(game_state)
        except Exception as e:
            logger.error("Failed to persist TOOL_CALL for %s: %s", tool_name, e, exc_info=True)

        # 3) Execute
        result = await self.event_bus.execute_command(command)
        if not result:
            raise RuntimeError(f"Command {type(command).__name__} returned None for {tool_name}")

        # 4/5) Broadcast & persist TOOL_RESULT if appropriate
        if isinstance(result, ToolResult):
            await self.event_bus.submit_command(
                BroadcastToolResultCommand(
                    game_id=game_state.game_id,
                    tool_name=tool_name,
                    result=result,
                ),
            )

            try:
                self.event_manager.add_event(
                    game_state=game_state,
                    event_type=GameEventType.TOOL_RESULT,
                    tool_name=tool_name,
                    result=result.model_dump(mode="json"),
                )
                self.save_manager.save_game(game_state)
            except Exception as e:
                logger.error("Failed to persist TOOL_RESULT for %s: %s", tool_name, e, exc_info=True)

        return result
