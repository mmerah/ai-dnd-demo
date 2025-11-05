"""Unit tests for `AIService`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

import pytest

from app.models.ai_response import CompleteResponse, ErrorResponse, NarrativeResponse, StreamEvent, StreamEventType
from app.services.ai.ai_service import AIService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.pipeline import Pipeline
from tests.factories import make_game_state


class _StubPipeline:
    """Stub pipeline for testing AIService."""

    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events

    async def execute(self, ctx: OrchestrationContext) -> AsyncIterator[StreamEvent]:
        """Execute stub pipeline - just yield pre-configured events."""
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_ai_service_yields_complete_response(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    expected_narrative = "Greetings"
    events = [StreamEvent(type=StreamEventType.COMPLETE, content=NarrativeResponse(narrative=expected_narrative))]
    service = AIService(pipeline=cast(Pipeline, _StubPipeline(events)))

    responses = [resp async for resp in service.generate_response("hi", game_state)]

    assert len(responses) == 1
    assert isinstance(responses[0], CompleteResponse)
    assert responses[0].narrative == expected_narrative


@pytest.mark.asyncio
async def test_ai_service_yields_error_response(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    events = [StreamEvent(type=StreamEventType.ERROR, content="failure")]
    service = AIService(pipeline=cast(Pipeline, _StubPipeline(events)))

    responses = [resp async for resp in service.generate_response("hi", game_state)]

    assert len(responses) == 1
    assert isinstance(responses[0], ErrorResponse)
    assert "failure" in responses[0].message
