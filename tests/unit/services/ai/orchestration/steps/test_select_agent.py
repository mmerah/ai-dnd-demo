"""Tests for SelectAgent step."""

import pytest

from app.agents.core.types import AgentType
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.select_agent import SelectAgent
from tests.factories import make_game_state


class TestSelectAgent:
    """Tests for SelectAgent step."""

    @pytest.mark.asyncio
    async def test_selects_narrative_agent(self) -> None:
        """Test selecting narrative agent when active_agent is NARRATIVE."""
        game_state = make_game_state(game_id="test-game")
        game_state.active_agent = AgentType.NARRATIVE

        ctx = OrchestrationContext(user_message="I look around", game_state=game_state)
        step = SelectAgent()

        result = await step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.selected_agent_type == AgentType.NARRATIVE

    @pytest.mark.asyncio
    async def test_selects_combat_agent(self) -> None:
        """Test selecting combat agent when active_agent is COMBAT."""
        game_state = make_game_state(game_id="test-game")
        game_state.active_agent = AgentType.COMBAT

        ctx = OrchestrationContext(user_message="I attack the goblin", game_state=game_state)
        step = SelectAgent()

        result = await step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.selected_agent_type == AgentType.COMBAT

    @pytest.mark.asyncio
    async def test_selects_npc_agent(self) -> None:
        """Test selecting NPC agent when active_agent is NPC."""
        game_state = make_game_state(game_id="test-game")
        game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(user_message="@innkeeper Hello", game_state=game_state)
        step = SelectAgent()

        result = await step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.selected_agent_type == AgentType.NPC

    @pytest.mark.asyncio
    async def test_preserves_other_context_fields(self) -> None:
        """Test that SelectAgent preserves other context fields."""
        game_state = make_game_state(game_id="test-game")
        game_state.active_agent = AgentType.NARRATIVE

        ctx = OrchestrationContext(
            user_message="I look around",
            game_state=game_state,
            context_text="existing context",
        )
        step = SelectAgent()

        result = await step.run(ctx)

        assert result.context.user_message == "I look around"
        assert result.context.context_text == "existing context"
        assert result.context.game_id == "test-game"
