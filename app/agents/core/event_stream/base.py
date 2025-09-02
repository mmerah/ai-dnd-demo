"""Base classes for event stream processing."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies

# We use object for event types because PydanticAI's event stream includes
# many internal event types that aren't exposed in their public API.
# We handle only the events we care about and ignore the rest.


class EventHandler(ABC):
    """Abstract base class for handling specific event types."""

    @abstractmethod
    async def can_handle(self, event: object) -> bool:
        """Check if this handler can process the given event."""

    @abstractmethod
    async def handle(self, event: object, context: "EventContext") -> None:
        """Process the event and update context as needed."""


@dataclass
class EventContext:
    """Context shared across event handlers."""

    game_id: str
    tool_calls_by_id: dict[str, str] = field(default_factory=dict)
    processed_tool_calls: set[str] = field(default_factory=set)

    def clear(self) -> None:
        """Clear the context for a new processing session."""
        self.tool_calls_by_id.clear()
        self.processed_tool_calls.clear()


class EventStreamProcessor:
    """
    Processes PydanticAI event streams using registered handlers.

    This class follows the Chain of Responsibility pattern, delegating
    event processing to specialized handlers based on event type.
    """

    def __init__(self, context: EventContext):
        """Initialize with a shared context."""
        self.context = context
        self.handlers: list[EventHandler] = []

    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        self.handlers.append(handler)

    async def process_stream(
        self,
        event_stream: AsyncIterable[object],
        ctx: RunContext[AgentDependencies] | None = None,
    ) -> None:
        """Process events from the stream using registered handlers."""
        async for event in event_stream:
            await self._process_single_event(event)

    async def _process_single_event(self, event: object) -> None:
        """Process a single event through the handler chain."""
        for handler in self.handlers:
            if await handler.can_handle(event):
                await handler.handle(event, self.context)
                # Continue to next handler - multiple handlers can process same event
