"""Integration tests combining `AIService` and `AgentOrchestrator`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.models.ai_response import CompleteResponse, NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState
from app.services.ai.ai_service import AIService
from app.services.ai.orchestrator_service import AgentOrchestrator
from tests.factories import make_game_state


class _StubSummarizer(BaseAgent):
    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:  # type: ignore[override]
        raise NotImplementedError


class _StubAgent(BaseAgent):
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events
        self.calls: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(self, message: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:
        self.calls.append(message)
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_ai_service_with_orchestrator_emits_response(monkeypatch: pytest.MonkeyPatch) -> None:
    narrative_events = [StreamEvent(type=StreamEventType.COMPLETE, content=NarrativeResponse(narrative="Hi"))]
    narrative_agent = _StubAgent(narrative_events)
    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = MagicMock()
    event_bus = MagicMock()
    game_service = MagicMock()

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", AsyncMock())
    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", AsyncMock())

    async def _empty_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if isinstance(kwargs, dict) and kwargs.get("yield_events"):
            yield StreamEvent(type=StreamEventType.COMPLETE, content="noop")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _empty_combat_loop)

    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer,  # type: ignore[arg-type]
        combat_service=combat_service,
        event_bus=event_bus,
        game_service=game_service,
    )

    ai_service = AIService(orchestrator)
    game_state = make_game_state()

    responses = [resp async for resp in ai_service.generate_response("hello", game_state)]

    assert responses and isinstance(responses[0], CompleteResponse)
    assert responses[0].narrative == "Hi"
    assert narrative_agent.calls == ["hello"]
    assert combat_agent.calls == []
