"""LoopStep for conditional iteration in orchestration pipeline."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.guards import Guard
from app.services.ai.orchestration.step import OrchestrationOutcome, Step, StepResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoopStep:
    """Execute steps repeatedly while guard is true (up to max_iterations)."""

    guard: Guard
    """Predicate evaluated before each iteration."""

    steps: Sequence[Step]
    """Steps to execute in each iteration."""

    max_iterations: int = 50
    """Safety cap to prevent infinite loops."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute steps in a loop while guard passes.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with CONTINUE and accumulated context updates
        """
        current_ctx = ctx
        iteration = 0

        guard_name = getattr(self.guard, "__name__", str(self.guard))
        logger.debug("LoopStep starting (guard='%s', max_iterations=%d)", guard_name, self.max_iterations)

        while iteration < self.max_iterations:
            # Check guard before iteration
            if not self.guard(current_ctx):
                logger.debug("LoopStep guard '%s' failed after %d iterations", guard_name, iteration)
                break

            iteration += 1
            logger.debug("LoopStep iteration %d/%d (guard '%s')", iteration, self.max_iterations, guard_name)

            # Execute all steps in this iteration
            for step in self.steps:
                step_name = step.__class__.__name__

                result = await step.run(current_ctx)
                current_ctx = result.context

                # Check for HALT or BRANCH
                if result.outcome == OrchestrationOutcome.HALT:
                    logger.info(
                        "LoopStep HALTED by %s (iteration %d): %s", step_name, iteration, result.reason or "no reason"
                    )
                    return result

                if result.outcome == OrchestrationOutcome.BRANCH:
                    logger.info(
                        "LoopStep BRANCHED by %s (iteration %d): %s", step_name, iteration, result.reason or "no reason"
                    )
                    return result

        # Loop terminated normally (guard failed or max iterations)
        if iteration >= self.max_iterations:
            logger.warning("LoopStep hit safety cap (%d iterations)", self.max_iterations)

        logger.debug("LoopStep completed (%d iterations, %d events)", iteration, len(current_ctx.events))

        return StepResult.continue_with(current_ctx)
