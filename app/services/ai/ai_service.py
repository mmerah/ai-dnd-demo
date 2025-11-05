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
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.pipeline import Pipeline

logger = logging.getLogger(__name__)


class AIService(IAIService):
    """Main AI Service that coordinates specialized agents via orchestration pipeline."""

    def __init__(self, pipeline: Pipeline) -> None:
        """Initialize AI Service with orchestration pipeline.

        Args:
            pipeline: The orchestration pipeline that handles agent routing and execution
        """
        settings = get_settings()
        self.debug_mode = settings.debug_ai
        self.pipeline = pipeline

    async def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        logger.info("AIService.generate_response called with stream=%s, game_id=%s", stream, game_state.game_id)
        try:
            # Create initial orchestration context
            # Capture combat_was_active flag for transition detection
            initial_ctx = OrchestrationContext(
                user_message=user_message,
                game_state=game_state,
                flags=OrchestrationFlags(combat_was_active=game_state.combat.is_active),
            )

            # Execute pipeline and process events
            event_count = 0
            async for event in self.pipeline.execute(initial_ctx):
                event_count += 1
                logger.debug("AIService received event %d: type=%s", event_count, event.type)

                # Convert StreamEvent to the expected format
                if event.type == StreamEventType.NARRATIVE_CHUNK:
                    if isinstance(event.content, str):
                        logger.debug("Yielding narrative_chunk: '%s...'", event.content[:30])
                        # Currently we don't forward chunks; SSE is the source of truth
                        pass
                elif event.type == StreamEventType.COMPLETE:
                    if isinstance(event.content, NarrativeResponse):
                        response = event.content
                        logger.info(
                            "Yielding complete event with narrative length: %d",
                            len(response.narrative) if response.narrative else 0,
                        )
                        yield CompleteResponse(
                            narrative=response.narrative
                            if response.narrative
                            else "I couldn't generate a response. Please try again.",
                        )
                elif event.type == StreamEventType.ERROR:
                    error_msg = str(event.content)
                    logger.error("Yielding error event: %s", error_msg)
                    yield ErrorResponse(message=f"Failed to generate response: {error_msg}")
            logger.info("AIService.generate_response completed. Total events: %d", event_count)
        except Exception as e:
            logger.error("Error in generate_response: %s", e, exc_info=True)
            yield ErrorResponse(message=f"Failed to generate response: {e!s}")
            # Fail fast
            raise
