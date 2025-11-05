"""Tests for BroadcastPrompt step."""

from unittest.mock import AsyncMock, create_autospec

import pytest

from app.interfaces.events import IEventBus
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.broadcast_prompt import BroadcastPrompt
from tests.factories import make_game_state


class TestBroadcastPrompt:
    """Tests for BroadcastPrompt step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.event_bus.submit_and_wait = AsyncMock()
        self.step = BroadcastPrompt(self.event_bus)

    @pytest.mark.asyncio
    async def test_broadcasts_with_auto_combat_prefix(self) -> None:
        """Test that step broadcasts with [Auto Combat] prefix."""
        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="Goblin attacks the player!",
        )

        await self.step.run(ctx)

        # Verify broadcast
        assert self.event_bus.submit_and_wait.called
        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == "[Auto Combat] Goblin attacks the player!"

    @pytest.mark.asyncio
    async def test_handles_empty_prompt(self) -> None:
        """Test that step handles empty prompt gracefully."""
        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            current_prompt="",
        )

        result = await self.step.run(ctx)

        # Should not broadcast for empty prompt
        assert not self.event_bus.submit_and_wait.called
        assert result.outcome == OrchestrationOutcome.CONTINUE
