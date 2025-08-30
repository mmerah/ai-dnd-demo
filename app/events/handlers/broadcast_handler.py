"""Handler for broadcasting events to frontend via SSE."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import (
    BroadcastCharacterUpdateCommand,
    BroadcastGameUpdateCommand,
    BroadcastNarrativeCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.models.game_state import GameState
from app.models.sse_events import (
    CharacterUpdateData,
    GameUpdateData,
    NarrativeData,
    SSEEventType,
    ToolCallData,
    ToolResultData,
)
from app.services.broadcast_service import broadcast_service

logger = logging.getLogger(__name__)


class BroadcastHandler(BaseHandler):
    """Handler for broadcasting events to frontend via SSE."""

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle broadcast commands."""
        result = CommandResult(success=True)

        if isinstance(command, BroadcastNarrativeCommand):
            narrative_data = NarrativeData(
                word=command.content if command.is_chunk else None,
                complete=True if command.is_complete else None,
                start=True if not command.is_chunk and not command.is_complete else None,
                content=command.content
                if not command.is_chunk and not command.is_complete and command.content
                else None,
            )
            await broadcast_service.publish(command.game_id, SSEEventType.NARRATIVE, narrative_data)
            logger.debug(f"Broadcast narrative: chunk={command.is_chunk}, complete={command.is_complete}")

        elif isinstance(command, BroadcastToolCallCommand):
            tool_call_data = ToolCallData(tool_name=command.tool_name, parameters=command.parameters)
            await broadcast_service.publish(command.game_id, SSEEventType.TOOL_CALL, tool_call_data)
            logger.debug(f"Broadcast tool call: {command.tool_name}")

        elif isinstance(command, BroadcastToolResultCommand):
            tool_result_data = ToolResultData(tool_name=command.tool_name, result=command.result)
            await broadcast_service.publish(command.game_id, SSEEventType.TOOL_RESULT, tool_result_data)
            logger.debug(f"Broadcast tool result: {command.tool_name}")

        elif isinstance(command, BroadcastCharacterUpdateCommand):
            character_dict = game_state.character.model_dump()
            character_update_data = CharacterUpdateData(character=character_dict)
            await broadcast_service.publish(command.game_id, SSEEventType.CHARACTER_UPDATE, character_update_data)
            logger.debug("Broadcast character update")

        elif isinstance(command, BroadcastGameUpdateCommand):
            game_state_dict = game_state.model_dump()
            game_update_data = GameUpdateData(game_state=game_state_dict)
            await broadcast_service.publish(command.game_id, SSEEventType.GAME_UPDATE, game_update_data)
            logger.debug("Broadcast game state update")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(
            command,
            BroadcastNarrativeCommand
            | BroadcastToolCallCommand
            | BroadcastToolResultCommand
            | BroadcastGameUpdateCommand
            | BroadcastCharacterUpdateCommand,
        )
