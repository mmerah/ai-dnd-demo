"""Centralized message display service following SOLID principles."""

import logging
from collections.abc import AsyncGenerator

from app.common.types import JSONSerializable
from app.interfaces.services import IBroadcastService, IMessageService
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.scenario import Scenario
from app.models.sse_events import (
    CharacterUpdateData,
    CompleteData,
    ErrorData,
    GameUpdateData,
    InitialNarrativeData,
    NarrativeData,
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
        """
        Send narrative content to the chat.

        Args:
            game_id: Game identifier
            content: Narrative text or chunk
            is_chunk: Whether this is a streaming chunk
            is_complete: Whether the narrative is complete
        """
        data = NarrativeData(
            word=content if is_chunk else None,
            complete=True if is_complete else None,
            start=True if not is_chunk and not is_complete else None,
            content=content if not is_chunk and not is_complete and content else None,
        )
        await self.broadcast_service.publish(game_id, SSEEventType.NARRATIVE.value, data)

    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, JSONSerializable]) -> None:
        """
        Send tool call information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool being called
            parameters: Tool parameters
        """
        data = ToolCallData(tool_name=tool_name, parameters=parameters)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_CALL.value, data)

    async def send_tool_result(self, game_id: str, tool_name: str, result: ToolResult) -> None:
        """
        Send tool result information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool that was called
            result: Result from the tool
        """
        data = ToolResultData(tool_name=tool_name, result=result)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_RESULT.value, data)

    async def send_character_update(self, game_id: str, character: CharacterSheet) -> None:
        """
        Send character sheet update.

        Args:
            game_id: Game identifier
            character: CharacterSheet instance
        """
        data = CharacterUpdateData(character=character)
        await self.broadcast_service.publish(game_id, SSEEventType.CHARACTER_UPDATE.value, data)

    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        """
        Send error message to the chat.

        Args:
            game_id: Game identifier
            error: Error message
            error_type: Type of error if available
        """
        data = ErrorData(error=error, type=error_type)
        await self.broadcast_service.publish(game_id, SSEEventType.ERROR.value, data)

    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        """
        Send complete game state update.

        Args:
            game_id: Game identifier
            game_state: GameState instance
        """
        data = GameUpdateData(game_state=game_state)
        await self.broadcast_service.publish(game_id, SSEEventType.GAME_UPDATE.value, data)

    async def send_complete(self, game_id: str) -> None:
        """
        Send completion event indicating processing is done.

        Args:
            game_id: Game identifier
        """
        data = CompleteData(status="success")
        await self.broadcast_service.publish(game_id, SSEEventType.COMPLETE.value, data)

    async def generate_sse_events(
        self,
        game_id: str,
        game_state: GameState,
        scenario: Scenario | None = None,
        available_scenarios: list[Scenario] | None = None,
    ) -> AsyncGenerator[dict[str, str], None]:
        """
        Generate SSE events for a client connection.

        This includes initial events (narrative, game state, scenario info) followed by
        subscribing to the broadcast service for ongoing events.

        Args:
            game_id: Game identifier
            game_state: Current game state
            scenario: Current scenario if available
            available_scenarios: List of available scenarios

        Yields:
            SSE formatted event dictionaries
        """
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

        # Send scenario info if available
        if scenario and available_scenarios:
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
