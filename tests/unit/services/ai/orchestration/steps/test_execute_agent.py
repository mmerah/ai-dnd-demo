"""Tests for ExecuteAgent step."""

import pytest

from app.agents.core.types import AgentType
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.execute_agent import ExecuteAgent
from tests.factories import make_game_state, make_multi_event_agent, make_stub_agent


class TestExecuteAgent:
    """Tests for ExecuteAgent step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.narrative_agent = make_stub_agent("Narrative response")
        self.combat_agent = make_stub_agent("Combat response")
        self.step = ExecuteAgent(self.narrative_agent, self.combat_agent)

    @pytest.mark.asyncio
    async def test_executes_narrative_agent(self) -> None:
        """Test executing narrative agent."""
        ctx = OrchestrationContext(
            user_message="I look around",
            game_state=self.game_state,
            selected_agent_type=AgentType.NARRATIVE,
            context_text="Narrative context",
        )
        result = await self.step.run(ctx)
        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 1
        assert result.context.events[0].content == "Narrative response"
        assert len(self.narrative_agent.process_calls) == 1

    @pytest.mark.asyncio
    async def test_executes_combat_agent(self) -> None:
        """Test executing combat agent."""
        ctx = OrchestrationContext(
            user_message="I attack",
            game_state=self.game_state,
            selected_agent_type=AgentType.COMBAT,
            context_text="Combat context",
        )
        result = await self.step.run(ctx)
        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 1
        assert result.context.events[0].content == "Combat response"
        assert len(self.combat_agent.process_calls) == 1

    @pytest.mark.asyncio
    async def test_requires_agent_type_selected(self) -> None:
        """Test that step requires agent type to be selected."""
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state, context_text="Context")

        with pytest.raises(ValueError, match="Agent type not selected"):
            await self.step.run(ctx)

    @pytest.mark.asyncio
    async def test_accumulates_multiple_events(self) -> None:
        """Test that step accumulates all events from agent."""
        multi_agent = make_multi_event_agent(["Event 1", "Event 2", "Event 3"])
        step = ExecuteAgent(multi_agent, self.combat_agent)
        ctx = OrchestrationContext(
            user_message="Test",
            game_state=self.game_state,
            selected_agent_type=AgentType.NARRATIVE,
            context_text="Context",
        )

        result = await step.run(ctx)

        assert len(result.context.events) == 3
        assert result.context.events[0].content == "Event 1"
        assert result.context.events[1].content == "Event 2"
        assert result.context.events[2].content == "Event 3"
