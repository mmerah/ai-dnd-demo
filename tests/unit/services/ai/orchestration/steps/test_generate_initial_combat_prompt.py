"""Tests for GenerateInitialCombatPrompt step."""

from unittest.mock import create_autospec

import pytest

from app.interfaces.services.game import ICombatService
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.generate_initial_combat_prompt import (
    GenerateInitialCombatPrompt,
)
from tests.factories import make_game_state


class TestGenerateInitialCombatPrompt:
    """Tests for GenerateInitialCombatPrompt step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.combat_service = create_autospec(ICombatService, instance=True)
        self.step = GenerateInitialCombatPrompt(self.combat_service)

    @pytest.mark.asyncio
    async def test_generates_prompt_via_service(self) -> None:
        """Test that step calls combat_service.generate_combat_prompt."""
        self.combat_service.generate_combat_prompt.return_value = "Combat begins! Roll initiative."

        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        self.combat_service.generate_combat_prompt.assert_called_once_with(self.game_state)
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_stores_prompt_in_context(self) -> None:
        """Test that step stores prompt in ctx.current_prompt."""
        self.combat_service.generate_combat_prompt.return_value = "Combat begins! Roll initiative."

        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.context.current_prompt == "Combat begins! Roll initiative."

    @pytest.mark.asyncio
    async def test_handles_empty_prompt(self) -> None:
        """Test that step handles empty prompt gracefully."""
        self.combat_service.generate_combat_prompt.return_value = ""

        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.context.current_prompt == ""
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_does_not_pass_tracking_params(self) -> None:
        """Test that step does not pass last_entity_id or last_round params."""
        self.combat_service.generate_combat_prompt.return_value = "Combat starts"

        # Set tracking flags (should be ignored for initial prompt)
        flags = OrchestrationFlags(
            last_prompted_entity_id="player-1",
            last_prompted_round=5,
        )
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            flags=flags,
        )

        await self.step.run(ctx)

        # Verify service called with only game_state (no tracking params)
        self.combat_service.generate_combat_prompt.assert_called_once_with(self.game_state)
