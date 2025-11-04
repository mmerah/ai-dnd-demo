"""Pipeline and PipelineBuilder for declarative orchestration composition."""

import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.guards import Guard
from app.services.ai.orchestration.loop import LoopStep
from app.services.ai.orchestration.step import OrchestrationOutcome, Step, StepResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConditionalStep:
    """A step that only executes when its guard predicate returns True.

    Wraps a guard and a list of steps to execute conditionally.
    """

    guard: Guard
    """Predicate function that determines whether to execute the steps."""

    steps: Sequence[Step]
    """Steps to execute if guard returns True."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute steps if guard passes, otherwise continue with current context.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult from the last executed step, or CONTINUE if guard fails
        """
        guard_name = getattr(self.guard, "__name__", str(self.guard))
        guard_result = self.guard(ctx)

        if not guard_result:
            logger.debug(
                "ConditionalStep guard '%s' failed, skipping %d steps",
                guard_name,
                len(self.steps),
            )
            return StepResult.continue_with(ctx)

        logger.info(
            "ConditionalStep guard '%s' passed, executing %d steps",
            guard_name,
            len(self.steps),
        )

        current_ctx = ctx
        for step in self.steps:
            step_name = step.__class__.__name__
            logger.info("  → Executing conditional step: %s", step_name)

            result = await step.run(current_ctx)
            current_ctx = result.context

            # If any step halts or branches, stop executing and return that result
            if result.outcome != OrchestrationOutcome.CONTINUE:
                logger.info(
                    "  ← Conditional step %s returned %s, stopping execution",
                    step_name,
                    result.outcome.value,
                )
                return result

        return StepResult.continue_with(current_ctx)


class Pipeline:
    """Immutable pipeline of orchestration steps.

    Executes steps in order, handling CONTINUE/HALT/BRANCH outcomes.
    Steps can be unconditional, conditional (ConditionalStep), or looped (LoopStep).
    """

    def __init__(self, steps: Sequence[Step | ConditionalStep | LoopStep]) -> None:
        """Initialize pipeline with steps.

        Args:
            steps: Ordered sequence of steps to execute (unconditional, conditional, or looped)
        """
        self._steps = steps

    async def execute(self, ctx: OrchestrationContext) -> AsyncIterator[StreamEvent]:
        """Execute the pipeline with the given context.

        Iterates through steps, executing each in order. Handles outcomes:
        - CONTINUE: Proceed to next step
        - HALT: Stop pipeline execution immediately
        - BRANCH: Reserved for future use (currently stops execution)

        Args:
            ctx: Initial orchestration context

        Yields:
            StreamEvents accumulated during pipeline execution

        Raises:
            Exception: Any unhandled exception from step execution
        """
        logger.info(
            "Starting pipeline execution for game_id=%s with %d steps",
            ctx.game_id,
            len(self._steps),
        )

        current_ctx = ctx

        for i, step in enumerate(self._steps):
            step_name = step.__class__.__name__
            logger.info(
                "Pipeline step %d/%d: %s",
                i + 1,
                len(self._steps),
                step_name,
            )

            try:
                result = await step.run(current_ctx)
                current_ctx = result.context

                # Handle outcome
                if result.outcome == OrchestrationOutcome.HALT:
                    logger.info(
                        "Pipeline HALTED at step %d/%d (%s): %s",
                        i + 1,
                        len(self._steps),
                        step_name,
                        result.reason or "no reason provided",
                    )
                    break

                elif result.outcome == OrchestrationOutcome.BRANCH:
                    logger.info(
                        "Pipeline BRANCHED at step %d/%d (%s): %s",
                        i + 1,
                        len(self._steps),
                        step_name,
                        result.reason or "no reason provided",
                    )
                    # For now, treat BRANCH as HALT (future: implement branching logic)
                    break

                # CONTINUE: proceed to next step
                logger.info(
                    "Step %s completed successfully (CONTINUE)",
                    step_name,
                )

            except Exception as exc:
                logger.error(
                    "Pipeline step %d/%d (%s) raised exception: %s",
                    i + 1,
                    len(self._steps),
                    step_name,
                    exc,
                    exc_info=True,
                )
                # Re-raise (fail fast)
                raise

        logger.info(
            "Pipeline execution completed for game_id=%s: %d events",
            current_ctx.game_id,
            len(current_ctx.events),
        )

        # Yield all accumulated events
        for event in current_ctx.events:
            yield event


class PipelineBuilder:
    """Builder for constructing orchestration pipelines declaratively.

    Provides ergonomic methods for assembling pipelines with conditional logic
    and looping constructs.
    """

    def __init__(self) -> None:
        """Initialize an empty pipeline builder."""
        self._steps: list[Step | ConditionalStep | LoopStep] = []

    def step(self, step_instance: Step) -> "PipelineBuilder":
        """Append an unconditional step to the pipeline.

        Args:
            step_instance: Step to execute unconditionally

        Returns:
            Self for method chaining
        """
        self._steps.append(step_instance)
        return self

    def when(self, guard: Guard, steps: Sequence[Step]) -> "PipelineBuilder":
        """Append a conditional group of steps to the pipeline.

        The steps will only execute if the guard predicate returns True.

        Args:
            guard: Predicate function to evaluate
            steps: Steps to execute if guard passes

        Returns:
            Self for method chaining
        """
        conditional = ConditionalStep(guard=guard, steps=steps)
        self._steps.append(conditional)
        return self

    def build(self) -> Pipeline:
        """Build the immutable Pipeline from accumulated steps.

        Returns:
            Pipeline ready for execution
        """
        return Pipeline(steps=self._steps)
