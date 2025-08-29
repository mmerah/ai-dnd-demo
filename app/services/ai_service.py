"""Main AI Service orchestrator following Single Responsibility."""

import logging
from collections.abc import AsyncIterator

from app.agents.base import BaseAgent
from app.config import get_settings
from app.interfaces.services import IAIService, IGameService
from app.models.ai_response import AIResponse, NarrativeResponse, StreamEventType
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class AIService(IAIService):
    """Main AI Service that coordinates specialized agents."""

    def __init__(self, game_service: IGameService) -> None:
        """Initialize AI Service."""
        settings = get_settings()
        self.debug_mode = settings.debug_ai
        self.game_service = game_service
        self.narrative_agent: BaseAgent | None = None  # Will be set by dependency provider

    async def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        """
        Generate AI response with streaming support.

        Args:
            user_message: The player's input
            game_state: Current game state
            game_service: Game service instance
            stream: Whether to stream the response

        Yields:
            Dict with response chunks or complete response
        """
        logger.info(f"AIService.generate_response called with stream={stream}")
        try:
            # Process through the narrative agent with event bus
            event_count = 0
            if not self.narrative_agent:
                raise RuntimeError("Narrative agent not initialized")
            async for event in self.narrative_agent.process(user_message, game_state, game_service, stream):
                event_count += 1
                logger.debug(f"AIService received event {event_count}: type={event.type}")

                # Convert StreamEvent to the expected format
                if event.type == StreamEventType.NARRATIVE_CHUNK:
                    logger.debug(f"Yielding narrative_chunk: '{event.content[:30]}...'")
                    yield {"type": "narrative_chunk", "content": event.content}
                elif event.type == StreamEventType.COMPLETE:
                    response: NarrativeResponse = event.content
                    logger.info(
                        f"Yielding complete event with narrative length: {len(response.narrative) if response.narrative else 0}"
                    )
                    yield {
                        "type": "complete",
                        "narrative": response.narrative
                        if response.narrative
                        else "I couldn't generate a response. Please try again.",
                    }
                elif event.type == StreamEventType.ERROR:
                    logger.error(f"Yielding error event: {event.content}")
                    yield {
                        "type": "error",
                        "message": f"Failed to generate response: {event.content}",
                    }
            logger.info(f"AIService.generate_response completed. Total events: {event_count}")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"Failed to generate response: {str(e)}",
            }
            # Fail fast
            raise
