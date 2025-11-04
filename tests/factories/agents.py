"""Factory helpers for creating test agents."""

from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent, ToolFunction
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import GameState


class StubAgent(BaseAgent):
    """Generic stub agent for testing.

    Records process calls and yields configurable response content.
    Useful for testing orchestration steps that execute agents.
    """

    def __init__(self, response_content: str = "Test response") -> None:
        """Initialize with configurable response content.

        Args:
            response_content: Content to yield as NARRATIVE_CHUNK event
        """
        self.response_content = response_content
        self.process_calls: list[tuple[str, GameState, str]] = []

    def get_required_tools(self) -> list[ToolFunction]:
        """Return empty tools list."""
        return []

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        context: str,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Record call and yield a single narrative chunk.

        Args:
            user_message: User's message/action
            game_state: Current game state
            context: Agent context string
            stream: Whether to stream events

        Yields:
            Single NARRATIVE_CHUNK event with response_content
        """
        self.process_calls.append((user_message, game_state, context))
        yield StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content=self.response_content)


class MultiEventAgent(BaseAgent):
    """Stub agent that yields multiple events for testing event accumulation."""

    def __init__(self, events: list[str]) -> None:
        """Initialize with list of event contents.

        Args:
            events: List of event content strings to yield
        """
        self.events = events
        self.process_calls: list[tuple[str, GameState, str]] = []

    def get_required_tools(self) -> list[ToolFunction]:
        """Return empty tools list."""
        return []

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        context: str,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Yield multiple narrative chunks.

        Args:
            user_message: User's message/action
            game_state: Current game state
            context: Agent context string
            stream: Whether to stream events

        Yields:
            Multiple NARRATIVE_CHUNK events
        """
        self.process_calls.append((user_message, game_state, context))
        for event_content in self.events:
            yield StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content=event_content)


def make_stub_agent(response_content: str = "Test response") -> StubAgent:
    """Create a stub agent for testing.

    Args:
        response_content: Content to yield when agent processes

    Returns:
        StubAgent instance
    """
    return StubAgent(response_content)


def make_multi_event_agent(events: list[str]) -> MultiEventAgent:
    """Create a multi-event stub agent for testing.

    Args:
        events: List of event content strings to yield

    Returns:
        MultiEventAgent instance
    """
    return MultiEventAgent(events)
