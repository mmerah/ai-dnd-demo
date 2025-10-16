"""Handler for broadcasting events to frontend via SSE."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import (
    BroadcastCombatSuggestionCommand,
    BroadcastGameUpdateCommand,
    BroadcastNarrativeCommand,
    BroadcastNPCDialogueCommand,
    BroadcastPolicyWarningCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.ai import IMessageService
from app.models.combat import CombatSuggestion
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class BroadcastHandler(BaseHandler):
    """Handler for broadcasting events to frontend via SSE."""

    def __init__(self, message_service: IMessageService) -> None:
        """Initialize with message service dependency."""
        self.message_service = message_service
        self.supported_commands = (
            BroadcastNarrativeCommand,
            BroadcastToolCallCommand,
            BroadcastToolResultCommand,
            BroadcastNPCDialogueCommand,
            BroadcastGameUpdateCommand,
            BroadcastPolicyWarningCommand,
            BroadcastCombatSuggestionCommand,
        )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle broadcast commands."""
        result = CommandResult()

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

        elif isinstance(command, BroadcastNPCDialogueCommand):
            await self.message_service.send_npc_dialogue(
                command.game_id,
                command.npc_id,
                command.npc_name,
                command.content,
                complete=command.complete,
            )
            logger.debug("Broadcast NPC dialogue")

        elif isinstance(command, BroadcastGameUpdateCommand):
            await self.message_service.send_game_update(
                command.game_id,
                game_state,
            )
            logger.debug("Broadcast game state update")

        elif isinstance(command, BroadcastPolicyWarningCommand):
            await self.message_service.send_policy_warning(
                command.game_id, command.message, command.tool_name, command.agent_type
            )
            logger.debug("Broadcast policy warning")

        elif isinstance(command, BroadcastCombatSuggestionCommand):
            suggestion = CombatSuggestion(
                suggestion_id=command.suggestion_id,
                npc_id=command.npc_id,
                npc_name=command.npc_name,
                action_text=command.action_text,
            )
            await self.message_service.send_combat_suggestion(
                command.game_id,
                suggestion,
            )
            logger.debug(f"Broadcast combat suggestion from {command.npc_name}")

        return result
