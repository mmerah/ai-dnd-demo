"""Set combat phase step for explicit combat state tracking."""

import logging

from app.models.combat import CombatPhase
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class SetCombatPhase:
    """Set the combat phase in game state."""

    def __init__(self, target_phase: CombatPhase) -> None:
        """Initialize with target phase."""
        self.target_phase = target_phase

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Set the combat phase in game state."""
        old_phase = ctx.game_state.combat.phase
        ctx.game_state.combat.phase = self.target_phase

        logger.info("Combat phase: %s → %s", old_phase.value, self.target_phase.value)

        return StepResult.continue_with(ctx)
