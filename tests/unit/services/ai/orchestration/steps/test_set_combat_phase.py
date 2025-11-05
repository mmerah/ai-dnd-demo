"""Tests for SetCombatPhase step."""

import pytest

from app.models.combat import CombatPhase
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.set_combat_phase import SetCombatPhase
from tests.factories import make_game_state


class TestSetCombatPhase:
    """Tests for SetCombatPhase step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")

    @pytest.mark.asyncio
    async def test_sets_phase_correctly(self) -> None:
        """Test that step sets combat phase correctly."""
        self.game_state.combat.phase = CombatPhase.INACTIVE

        step = SetCombatPhase(target_phase=CombatPhase.ACTIVE)
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
        )

        result = await step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.combat.phase == CombatPhase.ACTIVE

    @pytest.mark.asyncio
    async def test_transitions_to_different_phases(self) -> None:
        """Test transitions to all combat phases."""
        for target_phase in [
            CombatPhase.INACTIVE,
            CombatPhase.STARTING,
            CombatPhase.ACTIVE,
            CombatPhase.AUTO_ENDING,
            CombatPhase.ENDED,
        ]:
            self.game_state.combat.phase = CombatPhase.INACTIVE

            step = SetCombatPhase(target_phase=target_phase)
            ctx = OrchestrationContext(
                user_message="Test",
                game_state=self.game_state,
            )

            result = await step.run(ctx)

            assert self.game_state.combat.phase == target_phase
            assert result.outcome == OrchestrationOutcome.CONTINUE
