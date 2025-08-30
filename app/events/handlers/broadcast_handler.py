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
from app.interfaces.services import IGameService, IMessageService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class BroadcastHandler(BaseHandler):
    """Handler for broadcasting events to frontend via SSE."""

    def __init__(self, game_service: IGameService, message_service: IMessageService) -> None:
        """Initialize with game service and message service dependencies."""
        super().__init__(game_service)
        self.message_service = message_service

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle broadcast commands."""
        result = CommandResult(success=True)

        if isinstance(command, BroadcastNarrativeCommand):
            await self.message_service.send_narrative(
                command.game_id,
                command.content,
                is_chunk=command.is_chunk,
                is_complete=command.is_complete,
            )
            logger.debug(f"Broadcast narrative: chunk={command.is_chunk}, complete={command.is_complete}")

        elif isinstance(command, BroadcastToolCallCommand):
            await self.message_service.send_tool_call(
                command.game_id,
                command.tool_name,
                command.parameters,
            )
            logger.debug(f"Broadcast tool call: {command.tool_name}")

        elif isinstance(command, BroadcastToolResultCommand):
            if command.result:
                await self.message_service.send_tool_result(
                    command.game_id,
                    command.tool_name,
                    command.result,
                )
                logger.debug(f"Broadcast tool result: {command.tool_name}")
            else:
                logger.warning(f"Tool result for {command.tool_name} is None, skipping broadcast")

        elif isinstance(command, BroadcastCharacterUpdateCommand):
            await self.message_service.send_character_update(
                command.game_id,
                game_state.character,
            )
            logger.debug("Broadcast character update")

        elif isinstance(command, BroadcastGameUpdateCommand):
            await self.message_service.send_game_update(
                command.game_id,
                game_state,
            )
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
