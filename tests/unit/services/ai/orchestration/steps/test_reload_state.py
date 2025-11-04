"""Tests for ReloadState step."""

from unittest.mock import create_autospec

import pytest

from app.interfaces.services.game import IGameService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.reload_state import ReloadState
from tests.factories import make_game_state


class TestReloadState:
    """Tests for ReloadState step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.game_service = create_autospec(IGameService, instance=True)
        self.step = ReloadState(self.game_service)

    @pytest.mark.asyncio
    async def test_successful_reload(self) -> None:
        """Test successful state reload."""
        reloaded_state = make_game_state(game_id="test-game")
        reloaded_state.combat.is_active = True  # Change something to verify reload
        self.game_service.get_game.return_value = reloaded_state

        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)
        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.game_state.combat.is_active
        self.game_service.get_game.assert_called_once_with("test-game")

    @pytest.mark.asyncio
    async def test_reload_failure_raises_exception(self) -> None:
        """Test that reload fails fast when reload fails (Phase 5.6 behavior)."""
        self.game_service.get_game.side_effect = Exception("Database error")
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

        with pytest.raises(Exception, match="Database error"):
            await self.step.run(ctx)
