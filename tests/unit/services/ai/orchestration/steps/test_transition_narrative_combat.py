"""Tests for TransitionNarrativeToCombat step."""

from unittest.mock import AsyncMock, create_autospec

import pytest

from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.models.game_state import MessageRole
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.transition_narrative_combat import TransitionNarrativeToCombat
from tests.factories import make_game_state


class TestTransitionNarrativeToCombat:
    """Tests for TransitionNarrativeToCombat step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.summarizer_agent = create_autospec(ISummarizerAgent, instance=True)
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.event_bus.submit_and_wait = AsyncMock()
        self.step = TransitionNarrativeToCombat(
            summarizer_agent=self.summarizer_agent,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_transition_with_summary(self) -> None:
        """Test transition generates and broadcasts summary."""
        self.summarizer_agent.summarize_for_combat = AsyncMock(return_value="Enemies appear, roll for initiative!")
        ctx = OrchestrationContext(user_message="I draw my sword", game_state=self.game_state)

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        # Verify summarizer was called
        self.summarizer_agent.summarize_for_combat.assert_called_once_with(self.game_state)
        # Verify event bus was called
        assert self.event_bus.submit_and_wait.called
        # Verify summary added to conversation history
        assert len(self.game_state.conversation_history) > 0
        last_message = self.game_state.conversation_history[-1]
        assert last_message.role == MessageRole.DM
        assert "Enemies appear" in last_message.content

    @pytest.mark.asyncio
    async def test_transition_no_summary(self) -> None:
        """Test transition when summarizer returns empty summary."""
        self.summarizer_agent.summarize_for_combat = AsyncMock(return_value=None)
        ctx = OrchestrationContext(user_message="I draw my sword", game_state=self.game_state)

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        # Event bus should not be called for empty summary
        assert not self.event_bus.submit_and_wait.called
