"""Tests for CombatAutoEnd step."""

from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService
from app.interfaces.services.game import IGameService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.combat_auto_end import CombatAutoEnd
from tests.factories import make_combat_state, make_game_state, make_stub_agent


class TestCombatAutoEnd:
    """Tests for CombatAutoEnd step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.game_state.combat = make_combat_state(is_active=True)

        self.combat_agent = make_stub_agent("Combat ends")
        self.context_service = create_autospec(IContextService, instance=True)
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.game_service = create_autospec(IGameService, instance=True)

        # Mock game service to return fresh state after reload
        self.game_service.get_game.return_value = self.game_state
        self.context_service.build_context.return_value = "combat_context"

        self.step = CombatAutoEnd(
            combat_agent=self.combat_agent,
            context_service=self.context_service,
            event_bus=self.event_bus,
            game_service=self.game_service,
        )

    @pytest.mark.asyncio
    async def test_no_op_when_combat_not_active(self) -> None:
        """Test step returns CONTINUE without executing when combat is not active."""
        self.game_state.combat.is_active = False
        ctx = OrchestrationContext(user_message="Hello", game_state=self.game_state)

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(self.combat_agent.process_calls) == 0

    @pytest.mark.asyncio
    async def test_broadcasts_system_message(self) -> None:
        """Test step broadcasts system message about auto-end."""
        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        await self.step.run(ctx)

        # Verify broadcast was called with auto-end message
        self.event_bus.submit_and_wait.assert_called_once()
        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert len(call_args) == 1
        assert "defeated" in call_args[0].content.lower()

    @pytest.mark.asyncio
    async def test_executes_combat_agent_with_end_prompt(self) -> None:
        """Test step executes combat agent with end combat prompt."""
        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        result = await self.step.run(ctx)

        # Verify agent was executed with end combat prompt
        assert len(self.combat_agent.process_calls) == 1
        prompt, game_state, context = self.combat_agent.process_calls[0]
        assert "all enemies have been defeated" in prompt.lower()
        assert "end_combat" in prompt.lower()
        assert game_state == self.game_state
        assert context == "combat_context"

        # Verify events were accumulated
        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 1

    @pytest.mark.asyncio
    async def test_builds_combat_context(self) -> None:
        """Test step builds context with COMBAT agent type."""
        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        await self.step.run(ctx)

        # Verify context was built with COMBAT agent type
        self.context_service.build_context.assert_called_once_with(self.game_state, AgentType.COMBAT)

    @pytest.mark.asyncio
    async def test_reloads_state_after_execution(self) -> None:
        """Test step reloads game state after agent execution."""
        reloaded_state = make_game_state(game_id="test-game")
        reloaded_state.combat.is_active = False  # Combat ended
        self.game_service.get_game.return_value = reloaded_state

        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)
        result = await self.step.run(ctx)

        # Verify state was reloaded
        self.game_service.get_game.assert_called_once_with("test-game")
        assert not result.context.game_state.combat.is_active
