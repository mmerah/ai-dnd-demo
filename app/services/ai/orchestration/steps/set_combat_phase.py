"""Set combat phase step for explicit combat state tracking."""

import logging

from app.models.combat import CombatPhase
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class SetCombatPhase:
    """Step that sets the combat phase to track combat lifecycle explicitly.

    This step updates the combat phase field in the game state and logs
    the transition for observability.
    """

    def __init__(self, target_phase: CombatPhase) -> None:
        """Initialize the step with the target phase.

        Args:
            target_phase: The combat phase to set
        """
        self.target_phase = target_phase

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Set the combat phase in game state.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with phase updated (CONTINUE outcome)
        """
        old_phase = ctx.game_state.combat.phase
        ctx.game_state.combat.phase = self.target_phase

        logger.info(
            "Combat phase transition: %s → %s (game_id=%s)",
            old_phase.value,
            self.target_phase.value,
            ctx.game_id,
        )

        return StepResult.continue_with(ctx)
