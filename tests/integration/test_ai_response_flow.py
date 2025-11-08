"""Integration tests combining AIService and Pipeline."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import create_autospec

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService
from app.interfaces.services.game import (
    ICombatService,
    IConversationService,
    IGameService,
    IMetadataService,
)
from app.models.ai_response import (
    CompleteResponse,
    NarrativeResponse,
    StreamEvent,
    StreamEventType,
)
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.ai_service import AIService
from app.services.ai.orchestration.default_pipeline import create_default_pipeline
from tests.factories import make_game_state


class _StubSummarizer(BaseAgent):
    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    async def process(
        self, prompt: str, game_state: GameState, context: str, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        raise NotImplementedError
        yield  # type: ignore[unreachable]


class _StubAgent(BaseAgent):
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events
        self.calls: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self, message: str, game_state: GameState, context: str, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        self.calls.append(message)
        for event in self.events:
            yield event


class _StubToolSuggestorAgent(BaseAgent):
    """Stub tool suggestor that returns empty suggestions."""

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self, prompt: str, game_state: GameState, context: str, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        yield StreamEvent(type=StreamEventType.COMPLETE, content=ToolSuggestions(suggestions=[]))


@pytest.mark.asyncio
async def test_ai_service_with_pipeline_emits_response() -> None:
    narrative_response = NarrativeResponse(narrative="Hi")
    narrative_events = [StreamEvent(type=StreamEventType.COMPLETE, content=narrative_response)]
    narrative_agent = _StubAgent(narrative_events)
    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    tool_suggestor_agent = _StubToolSuggestorAgent()

    # Create mock services
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)
    metadata_service = create_autospec(IMetadataService, instance=True)
    metadata_service.extract_targeted_npcs.return_value = []
    conversation_service = create_autospec(IConversationService, instance=True)
    agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
    context_service = create_autospec(IContextService, instance=True)
    context_service.build_context.return_value = ""

    # Create pipeline with stub agents and mock services
    pipeline = create_default_pipeline(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer,  # type: ignore[arg-type]
        tool_suggestor_agent=tool_suggestor_agent,  # type: ignore[arg-type]
        context_service=context_service,
        combat_service=combat_service,
        game_service=game_service,
        metadata_service=metadata_service,
        conversation_service=conversation_service,
        agent_lifecycle_service=agent_lifecycle,
        event_bus=event_bus,
    )

    ai_service = AIService(pipeline=pipeline)
    game_state = make_game_state()
    # Configure game_service.get_game to return the same state when called with the game_id
    game_service.get_game.return_value = game_state

    user_message = "hello"
    responses = [resp async for resp in ai_service.generate_response(user_message, game_state)]

    assert responses and isinstance(responses[0], CompleteResponse)
    assert responses[0].narrative == narrative_response.narrative
    assert narrative_agent.calls == [user_message]
    assert combat_agent.calls == []
