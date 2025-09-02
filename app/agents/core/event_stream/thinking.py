"""Handler for thinking/reasoning events from PydanticAI."""

import logging

from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, ThinkingPart, ThinkingPartDelta

from app.agents.core.event_stream.base import EventContext, EventHandler
from app.services.ai.event_logger_service import EventLoggerService

logger = logging.getLogger(__name__)


class ThinkingHandler(EventHandler):
    """Handles thinking/reasoning events from the AI."""

    def __init__(self, event_logger: EventLoggerService | None = None):
        self.event_logger = event_logger

    async def can_handle(self, event: object) -> bool:
        """Check if this is a thinking event."""
        if isinstance(event, PartStartEvent):
            return isinstance(event.part, ThinkingPart)
        if isinstance(event, PartDeltaEvent):
            return isinstance(event.delta, ThinkingPartDelta)
        return False

    async def handle(self, event: object, context: EventContext) -> None:
        """Process thinking event."""
        content = self._extract_thinking_content(event)
        if content and self.event_logger:
            self.event_logger.log_thinking(content)

    def _extract_thinking_content(self, event: object) -> str | None:
        """Extract thinking content from the event."""
        if isinstance(event, PartStartEvent) and isinstance(event.part, ThinkingPart):
            # ThinkingPart always has content: str
            return event.part.content
        elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, ThinkingPartDelta):
            return event.delta.content_delta if event.delta.content_delta else None
        return None
