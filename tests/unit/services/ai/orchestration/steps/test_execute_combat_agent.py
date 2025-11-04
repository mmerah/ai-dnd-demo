"""Tests for ExecuteCombatAgent step."""

from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEventType
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.execute_combat_agent import ExecuteCombatAgent
from tests.factories import make_game_state, make_multi_event_agent, make_stub_agent


class TestExecuteCombatAgent:
    """Tests for ExecuteCombatAgent step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.combat_agent = make_stub_agent("Combat action executed")
        self.context_service = create_autospec(IContextService, instance=True)
        self.step = ExecuteCombatAgent(self.combat_agent, self.context_service)

    @pytest.mark.asyncio
    async def test_builds_combat_context(self) -> None:
        """Test that step builds combat context via context_service."""
        self.context_service.build_context.return_value = "Combat context with initiative"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="Goblin attacks!",
        )

        await self.step.run(ctx)

        self.context_service.build_context.assert_called_once_with(
            self.game_state,
            AgentType.COMBAT,
        )

    @pytest.mark.asyncio
    async def test_executes_combat_agent_with_prompt(self) -> None:
        """Test that step executes combat agent with ctx.current_prompt."""
        self.context_service.build_context.return_value = "Combat context"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="Goblin's turn to act!",
        )

        await self.step.run(ctx)

        # Verify agent was called
        assert len(self.combat_agent.process_calls) == 1
        call = self.combat_agent.process_calls[0]
        assert call[0] == "Goblin's turn to act!"
        assert call[2] == "Combat context"

    @pytest.mark.asyncio
    async def test_collects_events(self) -> None:
        """Test that step collects events from agent execution."""
        self.context_service.build_context.return_value = "Combat context"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="Test prompt",
        )

        result = await self.step.run(ctx)

        # Verify events collected
        assert len(result.context.events) == 1
        assert result.context.events[0].type == StreamEventType.NARRATIVE_CHUNK
        assert result.context.events[0].content == "Combat action executed"

    @pytest.mark.asyncio
    async def test_handles_empty_prompt(self) -> None:
        """Test that step handles empty prompt gracefully."""
        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="",
        )

        result = await self.step.run(ctx)

        # Should not call agent for empty prompt
        assert len(self.combat_agent.process_calls) == 0
        assert len(result.context.events) == 0
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_accumulates_multiple_events(self) -> None:
        """Test that step accumulates all events from agent."""
        multi_agent = make_multi_event_agent(["Event 1", "Event 2", "Event 3"])
        self.context_service.build_context.return_value = "Combat context"

        step = ExecuteCombatAgent(multi_agent, self.context_service)

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="Test prompt",
        )

        result = await step.run(ctx)

        assert len(result.context.events) == 3
        assert result.context.events[0].content == "Event 1"
        assert result.context.events[1].content == "Event 2"
        assert result.context.events[2].content == "Event 3"
