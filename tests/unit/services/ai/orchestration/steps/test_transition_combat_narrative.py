"""Tests for TransitionCombatToNarrative step."""

from unittest.mock import AsyncMock, create_autospec

import pytest

from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService
from app.models.game_state import MessageRole
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.transition_combat_narrative import TransitionCombatToNarrative
from tests.factories import make_game_state, make_multi_event_agent, make_stub_agent


class TestTransitionCombatToNarrative:
    """Tests for TransitionCombatToNarrative step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.summarizer_agent = create_autospec(ISummarizerAgent, instance=True)
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.event_bus.submit_and_wait = AsyncMock()
        self.context_service = create_autospec(IContextService, instance=True)
        self.context_service.build_context.return_value = "Narrative context"
        self.narrative_agent = make_stub_agent("The dust settles.")

        self.step = TransitionCombatToNarrative(
            summarizer_agent=self.summarizer_agent,
            event_bus=self.event_bus,
            context_service=self.context_service,
            narrative_agent=self.narrative_agent,
        )

    @pytest.mark.asyncio
    async def test_generates_summary_and_prompts_narrative_agent(self) -> None:
        """Test step generates summary, broadcasts it, and prompts narrative agent."""
        self.summarizer_agent.summarize_combat_end = AsyncMock(return_value="Victory!")
        ctx = OrchestrationContext(user_message="", game_state=self.game_state)

        result = await self.step.run(ctx)

        # Core behavior checks
        assert result.outcome == OrchestrationOutcome.CONTINUE
        self.summarizer_agent.summarize_combat_end.assert_called_once_with(self.game_state)

        # Summary added to conversation history
        assert any("[Summary:" in m.content and m.role == MessageRole.DM for m in self.game_state.conversation_history)

        # Broadcasts happened (summary + system message)
        assert self.event_bus.submit_and_wait.call_count == 2

        # Narrative agent called with aftermath prompt
        assert len(self.narrative_agent.process_calls) == 1
        prompt, _, context = self.narrative_agent.process_calls[0]
        assert "aftermath" in prompt.lower()

        # Events accumulated
        assert len(result.context.events) == 1

    @pytest.mark.asyncio
    async def test_no_summary_still_prompts_narrative_agent(self) -> None:
        """Test step still prompts narrative agent when summarizer returns None."""
        self.summarizer_agent.summarize_combat_end = AsyncMock(return_value=None)
        ctx = OrchestrationContext(user_message="", game_state=self.game_state)

        await self.step.run(ctx)

        # No summary added
        assert not any("[Summary:" in m.content for m in self.game_state.conversation_history)

        # Only system message broadcast (not summary)
        assert self.event_bus.submit_and_wait.call_count == 1

        # Narrative agent still called
        assert len(self.narrative_agent.process_calls) == 1

    @pytest.mark.asyncio
    async def test_accumulates_multiple_narrative_events(self) -> None:
        """Test that multiple events from narrative agent are accumulated."""
        self.summarizer_agent.summarize_combat_end = AsyncMock(return_value="Done")

        # Use multi-event agent
        narrative_agent = make_multi_event_agent(["Part 1", "Part 2", "Part 3"])
        step = TransitionCombatToNarrative(
            summarizer_agent=self.summarizer_agent,
            event_bus=self.event_bus,
            context_service=self.context_service,
            narrative_agent=narrative_agent,
        )

        ctx = OrchestrationContext(user_message="", game_state=self.game_state)
        result = await step.run(ctx)

        # All events accumulated
        assert len(result.context.events) == 3
