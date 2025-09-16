"""Unit tests for `AgentOrchestrator`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import GameState
from app.services.ai.orchestrator_service import AgentOrchestrator
from tests.factories import make_game_state


class _StubAgent(BaseAgent):
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events
        self.messages: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self, user_message: str, game_state: GameState, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        self.messages.append(user_message)
        for event in self.events:
            yield event


class _StubSummarizer(BaseAgent):
    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:  # type: ignore[override]
        raise NotImplementedError


@pytest.mark.asyncio
async def test_orchestrator_uses_narrative_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    narrative_events = [StreamEvent(type=StreamEventType.COMPLETE, content="done")]
    narrative_agent = _StubAgent(narrative_events)
    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = MagicMock()
    event_bus = MagicMock()
    game_service = MagicMock()

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", AsyncMock())

    async def _no_op_prompt(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", _no_op_prompt)

    async def _empty_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if kwargs.get("yield_events"):
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

    events = [event async for event in orchestrator.process("hello", game_state)]

    assert events == narrative_events
    assert narrative_agent.messages == ["hello"]
    assert combat_agent.messages == []


@pytest.mark.asyncio
async def test_orchestrator_handles_combat_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    narrative_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="narrative"),
        ]
    )
    combat_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="combat"),
        ]
    )
    summarizer = _StubSummarizer()
    combat_service = MagicMock()
    combat_service.generate_combat_prompt.return_value = "begin combat"
    event_bus = MagicMock()
    game_service = MagicMock()

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    reload_calls: list[bool] = [False]

    def _fake_reload(service: object, state: GameState) -> GameState:
        # first call toggles combat active
        state.combat.is_active = not reload_calls[0]
        reload_calls[0] = True
        return state

    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _fake_reload)
    mock_transition = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", mock_transition)
    mock_system_prompt = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", mock_system_prompt)

    async def _fake_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if kwargs.get("produce_loop"):
            yield StreamEvent(type=StreamEventType.COMPLETE, content="loop")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _fake_combat_loop)

    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer,  # type: ignore[arg-type]
        combat_service=combat_service,
        event_bus=event_bus,
        game_service=game_service,
    )

    events = [event async for event in orchestrator.process("advance", game_state)]

    assert any(evt.content == "combat" for evt in events)
    mock_transition.assert_awaited()
    combat_service.generate_combat_prompt.assert_called_once()
