"""Centralized message display service."""

import logging
from collections.abc import AsyncGenerator

from app.common.types import JSONSerializable
from app.interfaces.services.ai import IMessageService
from app.interfaces.services.common import IBroadcastService
from app.models.combat import CombatSuggestion
from app.models.game_state import GameState
from app.models.scenario import ScenarioSheet
from app.models.sse_events import (
    CombatSuggestionData,
    CompleteData,
    ErrorData,
    GameUpdateData,
    InitialNarrativeData,
    NarrativeData,
    NPCDialogueData,
    PolicyWarningData,
    ScenarioInfoData,
    SSEEvent,
    SSEEventType,
    ToolCallData,
    ToolResultData,
)
from app.models.tool_results import ToolResult

logger = logging.getLogger(__name__)


class MessageService(IMessageService):
    """Service for managing and broadcasting all game messages."""

    def __init__(self, broadcast_service: IBroadcastService) -> None:
        """Initialize with broadcast service dependency."""
        self.broadcast_service = broadcast_service

    async def send_narrative(
        self,
        game_id: str,
        content: str,
        is_chunk: bool = False,
        is_complete: bool = False,
    ) -> None:
        # For complete messages with content, send the content directly
        # Handles orchestrator's system messages
        if is_complete and content:
            data = NarrativeData(
                content=content,
                complete=True,
            )
        else:
            data = NarrativeData(
                word=content if is_chunk else None,
                complete=True if is_complete else None,
                start=True if not is_chunk and not is_complete else None,
                content=content if not is_chunk and not is_complete and content else None,
            )
        await self.broadcast_service.publish(game_id, SSEEventType.NARRATIVE.value, data)

    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, JSONSerializable]) -> None:
        data = ToolCallData(tool_name=tool_name, parameters=parameters)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_CALL.value, data)

    async def send_tool_result(self, game_id: str, tool_name: str, result: ToolResult) -> None:
        data = ToolResultData(tool_name=tool_name, result=result)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_RESULT.value, data)

    async def send_npc_dialogue(
        self,
        game_id: str,
        npc_id: str,
        npc_name: str,
        content: str,
        complete: bool = True,
    ) -> None:
        # Broadcast dedicated NPC dialogue payload so the frontend can render distinct styling.
        data = NPCDialogueData(
            npc_id=npc_id,
            npc_name=npc_name,
            content=content,
            complete=complete,
        )
        await self.broadcast_service.publish(game_id, SSEEventType.NPC_DIALOGUE.value, data)

    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        data = ErrorData(error=error, type=error_type)
        await self.broadcast_service.publish(game_id, SSEEventType.ERROR.value, data)

    async def send_policy_warning(
        self, game_id: str, message: str, tool_name: str | None, agent_type: str | None
    ) -> None:
        data = PolicyWarningData(message=message, tool_name=tool_name, agent_type=agent_type)
        await self.broadcast_service.publish(game_id, SSEEventType.POLICY_WARNING.value, data)

    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        data = GameUpdateData(game_state=game_state)
        await self.broadcast_service.publish(game_id, SSEEventType.GAME_UPDATE.value, data)

    async def send_combat_suggestion(self, game_id: str, suggestion: CombatSuggestion) -> None:
        """Broadcast a combat suggestion from an allied NPC."""
        data = CombatSuggestionData(suggestion=suggestion)
        await self.broadcast_service.publish(game_id, SSEEventType.COMBAT_SUGGESTION.value, data)

    async def send_complete(self, game_id: str) -> None:
        data = CompleteData(status="success")
        await self.broadcast_service.publish(game_id, SSEEventType.COMPLETE.value, data)

    async def generate_sse_events(
        self,
        game_id: str,
        game_state: GameState,
        scenario: ScenarioSheet,
        available_scenarios: list[ScenarioSheet],
    ) -> AsyncGenerator[dict[str, str], None]:
        logger.info(f"Client subscribed to SSE for game {game_id}")

        # Send initial narrative if exists
        if game_state.conversation_history:
            initial_event = SSEEvent(
                event=SSEEventType.INITIAL_NARRATIVE,
                data=InitialNarrativeData(
                    scenario_title=game_state.scenario_title or "Custom Adventure",
                    narrative=game_state.conversation_history[0].content,
                ),
            )
            yield initial_event.to_sse_format()

        # Send initial game state
        game_update_event = SSEEvent(
            event=SSEEventType.GAME_UPDATE,
            data=GameUpdateData(game_state=game_state),
        )
        yield game_update_event.to_sse_format()

        # Send scenario info
        scenario_event = SSEEvent(
            event=SSEEventType.SCENARIO_INFO,
            data=ScenarioInfoData(
                current_scenario=scenario,
                available_scenarios=available_scenarios,
            ),
        )
        yield scenario_event.to_sse_format()

        # Subscribe to ongoing events
        async for event_data in self.broadcast_service.subscribe(game_id):
            if event_data["event"] != "narrative":
                logger.debug(f"Sending SSE event '{event_data['event']}' to game {game_id}")
            yield event_data
