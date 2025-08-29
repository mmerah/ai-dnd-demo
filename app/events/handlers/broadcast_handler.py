"""Handler for broadcasting events to frontend via SSE."""

import json
import logging
from typing import Any

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
from app.services.broadcast_service import broadcast_service

logger = logging.getLogger(__name__)


class BroadcastHandler(BaseHandler):
    """Handler for broadcasting events to frontend via SSE."""

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle broadcast commands."""
        result = CommandResult(success=True)

        if isinstance(command, BroadcastNarrativeCommand):
            data: dict[str, Any] = {}
            if command.is_chunk:
                data["word"] = command.content
            elif command.is_complete:
                data["complete"] = True
            else:
                data["start"] = True
                if command.content:
                    data["content"] = command.content

            await broadcast_service.publish(command.game_id, "narrative", data)
            logger.debug(f"Broadcast narrative: chunk={command.is_chunk}, complete={command.is_complete}")

        elif isinstance(command, BroadcastToolCallCommand):
            await broadcast_service.publish(
                command.game_id,
                "tool_call",
                {
                    "tool_name": command.tool_name,
                    "parameters": command.parameters,
                    "timestamp": command.timestamp.isoformat(),
                },
            )
            logger.info(f"Broadcast tool call: {command.tool_name}")

        elif isinstance(command, BroadcastToolResultCommand):
            await broadcast_service.publish(
                command.game_id,
                "tool_result",
                {"tool_name": command.tool_name, "result": command.result, "timestamp": command.timestamp.isoformat()},
            )
            logger.info(f"Broadcast tool result: {command.tool_name}")

        elif isinstance(command, BroadcastCharacterUpdateCommand):
            character_data = game_state.character.model_dump()
            await broadcast_service.publish(command.game_id, "character_update", {"character": character_data})
            logger.debug("Broadcast character update")

        elif isinstance(command, BroadcastGameUpdateCommand):
            game_state_dict = json.loads(game_state.model_dump_json())
            await broadcast_service.publish(command.game_id, "game_update", game_state_dict)
            logger.debug("Broadcast game state update")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(
            command,
            (
                BroadcastNarrativeCommand,
                BroadcastToolCallCommand,
                BroadcastToolResultCommand,
                BroadcastGameUpdateCommand,
                BroadcastCharacterUpdateCommand,
            ),
        )
