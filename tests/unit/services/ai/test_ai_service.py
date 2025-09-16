"""Unit tests for `AIService`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

import pytest

from app.models.ai_response import CompleteResponse, ErrorResponse, NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState
from app.services.ai.ai_service import AIService
from app.services.ai.orchestrator_service import AgentOrchestrator
from tests.factories import make_game_state


class _StubOrchestrator:
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events

    async def process(
        self, user_message: str, game_state: GameState, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_ai_service_yields_complete_response(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    expected_narrative = "Greetings"
    events = [StreamEvent(type=StreamEventType.COMPLETE, content=NarrativeResponse(narrative=expected_narrative))]
    service = AIService(orchestrator=cast(AgentOrchestrator, _StubOrchestrator(events)))

    responses = [resp async for resp in service.generate_response("hi", game_state)]

    assert len(responses) == 1
    assert isinstance(responses[0], CompleteResponse)
    assert responses[0].narrative == expected_narrative


@pytest.mark.asyncio
async def test_ai_service_yields_error_response(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    events = [StreamEvent(type=StreamEventType.ERROR, content="failure")]
    service = AIService(orchestrator=cast(AgentOrchestrator, _StubOrchestrator(events)))

    responses = [resp async for resp in service.generate_response("hi", game_state)]

    assert len(responses) == 1
    assert isinstance(responses[0], ErrorResponse)
    assert "failure" in responses[0].message
