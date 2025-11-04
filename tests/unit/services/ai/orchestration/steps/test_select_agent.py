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
    async def test_parity_with_legacy_agent_router(self) -> None:
        """Test that SelectAgent produces same result as legacy agent_router.select()."""
        # This test ensures Phase 1b maintains parity with existing behavior
        from app.services.ai.orchestrator import agent_router

        # Test with NARRATIVE
        game_state_narrative = make_game_state(game_id="test-1")
        game_state_narrative.active_agent = AgentType.NARRATIVE
        legacy_result = agent_router.select(game_state_narrative)

        ctx_narrative = OrchestrationContext(user_message="test", game_state=game_state_narrative)
        step = SelectAgent()
        step_result = await step.run(ctx_narrative)

        assert step_result.context.selected_agent_type == legacy_result

        # Test with COMBAT
        game_state_combat = make_game_state(game_id="test-2")
        game_state_combat.active_agent = AgentType.COMBAT
        legacy_result = agent_router.select(game_state_combat)

        ctx_combat = OrchestrationContext(user_message="test", game_state=game_state_combat)
        step_result = await step.run(ctx_combat)

        assert step_result.context.selected_agent_type == legacy_result
