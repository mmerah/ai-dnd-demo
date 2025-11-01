"""Main AI Service orchestrator."""

import logging
from collections.abc import AsyncIterator

from app.config import get_settings
from app.interfaces.services.ai import IAIService
from app.models.ai_response import (
    AIResponse,
    CompleteResponse,
    ErrorResponse,
    NarrativeResponse,
    StreamEventType,
)
from app.models.game_state import GameState
from app.services.ai.orchestrator.orchestrator_service import AgentOrchestrator

logger = logging.getLogger(__name__)


class AIService(IAIService):
    """Main AI Service that coordinates specialized agents."""

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        """Initialize AI Service with agent orchestrator."""
        settings = get_settings()
        self.debug_mode = settings.debug_ai
        self.orchestrator = orchestrator

    async def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        logger.info(f"AIService.generate_response called with stream={stream}")
        try:
            # Route through the orchestrator (e.g., narrative vs combat)
            event_count = 0
            async for event in self.orchestrator.process(user_message, game_state, stream):
                event_count += 1
                logger.debug(f"AIService received event {event_count}: type={event.type}")

                # Convert StreamEvent to the expected format
                if event.type == StreamEventType.NARRATIVE_CHUNK:
                    if isinstance(event.content, str):
                        logger.debug(f"Yielding narrative_chunk: '{event.content[:30]}...'")
                        # Currently we don't forward chunks; SSE is the source of truth
                        pass
                elif event.type == StreamEventType.COMPLETE:
                    if isinstance(event.content, NarrativeResponse):
                        response = event.content
                        logger.info(
                            f"Yielding complete event with narrative length: {len(response.narrative) if response.narrative else 0}",
                        )
                        yield CompleteResponse(
                            narrative=response.narrative
                            if response.narrative
                            else "I couldn't generate a response. Please try again.",
                        )
                elif event.type == StreamEventType.ERROR:
                    error_msg = str(event.content)
                    logger.error(f"Yielding error event: {error_msg}")
                    yield ErrorResponse(message=f"Failed to generate response: {error_msg}")
            logger.info(f"AIService.generate_response completed. Total events: {event_count}")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            yield ErrorResponse(message=f"Failed to generate response: {e!s}")
            # Fail fast
            raise
