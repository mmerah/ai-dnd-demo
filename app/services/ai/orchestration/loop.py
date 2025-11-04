"""LoopStep for conditional iteration in orchestration pipeline.

This module provides LoopStep, which allows pipeline steps to be executed
repeatedly while a guard condition remains true. This is essential for
decomposing the combat loop into atomic steps.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.guards import Guard
from app.services.ai.orchestration.step import OrchestrationOutcome, Step, StepResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoopStep:
    """Execute steps repeatedly while a guard condition is true.

    LoopStep enables conditional iteration within the pipeline, essential for
    decomposing combat auto-run logic into atomic steps. The loop continues
    until:
    - Guard returns False
    - Any inner step returns HALT
    - Safety cap (max_iterations) is reached

    Attributes:
        guard: Predicate function evaluated before each iteration
        steps: Steps to execute in each iteration
        max_iterations: Safety cap to prevent infinite loops
    """

    guard: Guard
    """Predicate evaluated before each iteration. Loop continues while True."""

    steps: Sequence[Step]
    """Steps to execute in each iteration."""

    max_iterations: int = 50
    """Maximum iterations before loop terminates (safety cap)."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute steps in a loop while guard passes.

        The loop evaluates the guard before each iteration. If the guard passes,
        all steps execute sequentially. Context updates accumulate across iterations.

        Termination conditions:
        1. Guard returns False before iteration starts
        2. Any step returns HALT (breaks loop immediately)
        3. max_iterations reached (logged as warning)

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with CONTINUE outcome and accumulated context updates

        Note:
            - Guard is re-evaluated before each iteration
            - HALT from inner step propagates immediately (breaks loop)
            - BRANCH outcome treated as HALT (future: implement branching)
            - Context accumulates across all iterations
        """
        current_ctx = ctx
        iteration = 0

        guard_name = getattr(self.guard, "__name__", str(self.guard))

        logger.info(
            "LoopStep: Starting with max_iterations=%d, %d steps per iteration, guard='%s'",
            self.max_iterations,
            len(self.steps),
            guard_name,
        )

        while iteration < self.max_iterations:
            # Check guard before iteration
            guard_result = self.guard(current_ctx)
            if not guard_result:
                logger.info(
                    "LoopStep: Guard '%s' failed after %d iterations, exiting loop",
                    guard_name,
                    iteration,
                )
                break

            iteration += 1
            logger.info(
                "LoopStep: Iteration %d/%d starting (guard '%s' passed)", iteration, self.max_iterations, guard_name
            )

            # Execute all steps in this iteration
            for step_idx, step in enumerate(self.steps):
                step_name = step.__class__.__name__
                logger.info(
                    "LoopStep iteration %d: Executing step %d/%d: %s",
                    iteration,
                    step_idx + 1,
                    len(self.steps),
                    step_name,
                )

                result = await step.run(current_ctx)
                current_ctx = result.context

                # Check for HALT or BRANCH
                if result.outcome == OrchestrationOutcome.HALT:
                    logger.info(
                        "LoopStep HALTED by step %s at iteration %d: %s",
                        step_name,
                        iteration,
                        result.reason or "no reason provided",
                    )
                    # Propagate HALT to break out of loop
                    return result

                if result.outcome == OrchestrationOutcome.BRANCH:
                    logger.info(
                        "LoopStep BRANCHED by step %s at iteration %d: %s",
                        step_name,
                        iteration,
                        result.reason or "no reason provided",
                    )
                    # Treat BRANCH as HALT for now (future: implement branching)
                    return result

                # CONTINUE: proceed to next step in iteration

            logger.info("LoopStep: Iteration %d completed", iteration)

        # Loop terminated normally (guard failed or max iterations)
        if iteration >= self.max_iterations:
            logger.warning(
                "LoopStep hit safety cap of %d iterations",
                self.max_iterations,
            )

        logger.debug(
            "LoopStep completed: %d iterations, %d total events",
            iteration,
            len(current_ctx.events),
        )

        return StepResult.continue_with(current_ctx)
