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
    """A step that executes its steps only when its guard returns True."""

    guard: Guard
    """Predicate function that determines whether to execute the steps."""

    steps: Sequence[Step]
    """Steps to execute if guard returns True."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute steps if guard passes, otherwise continue with current context."""
        guard_name = getattr(self.guard, "__name__", str(self.guard))
        guard_result = self.guard(ctx)

        if not guard_result:
            logger.debug("Guard '%s' failed, skipping %d steps", guard_name, len(self.steps))
            return StepResult.continue_with(ctx)

        logger.debug("Guard '%s' passed, executing %d steps", guard_name, len(self.steps))

        current_ctx = ctx
        for step in self.steps:
            step_name = step.__class__.__name__
            logger.debug("  → Executing conditional step: %s", step_name)

            result = await step.run(current_ctx)
            current_ctx = result.context

            # If any step halts or branches, stop executing and return that result
            if result.outcome != OrchestrationOutcome.CONTINUE:
                logger.info("Step %s returned %s, stopping conditional execution", step_name, result.outcome.value)
                return result

        return StepResult.continue_with(current_ctx)


class Pipeline:
    """Immutable pipeline of orchestration steps.

    Executes steps in order, handling CONTINUE/HALT/BRANCH outcomes.
    """

    def __init__(self, steps: Sequence[Step | ConditionalStep | LoopStep]) -> None:
        """Initialize pipeline with ordered sequence of steps."""
        self._steps = steps

    async def execute(self, ctx: OrchestrationContext) -> AsyncIterator[StreamEvent]:
        """Execute the pipeline with the given context.

        Args:
            ctx: Initial orchestration context

        Yields:
            StreamEvents accumulated during pipeline execution
        """
        logger.info("Pipeline execution started (game_id=%s, %d steps)", ctx.game_id, len(self._steps))

        current_ctx = ctx

        for i, step in enumerate(self._steps):
            step_name = step.__class__.__name__
            logger.debug("Step %d/%d: %s", i + 1, len(self._steps), step_name)

            try:
                result = await step.run(current_ctx)
                current_ctx = result.context

                # Handle outcome
                if result.outcome == OrchestrationOutcome.HALT:
                    logger.info("Pipeline HALTED at %s: %s", step_name, result.reason or "no reason")
                    break

                elif result.outcome == OrchestrationOutcome.BRANCH:
                    logger.info("Pipeline BRANCHED at %s: %s", step_name, result.reason or "no reason")
                    break

            except Exception as exc:
                logger.error("Pipeline step %s raised exception: %s", step_name, exc, exc_info=True)
                raise

        logger.info(
            "Pipeline execution completed (game_id=%s, %d events)", current_ctx.game_id, len(current_ctx.events)
        )

        # Yield all accumulated events
        for event in current_ctx.events:
            yield event


class PipelineBuilder:
    """Builder for constructing orchestration pipelines declaratively."""

    def __init__(self) -> None:
        """Initialize an empty pipeline builder."""
        self._steps: list[Step | ConditionalStep | LoopStep] = []

    def step(self, step_instance: Step) -> "PipelineBuilder":
        """Append an unconditional step to the pipeline."""
        self._steps.append(step_instance)
        return self

    def when(self, guard: Guard, steps: Sequence[Step]) -> "PipelineBuilder":
        """Append a conditional group of steps (execute only if guard passes)."""
        conditional = ConditionalStep(guard=guard, steps=steps)
        self._steps.append(conditional)
        return self

    def build(self) -> Pipeline:
        """Build the immutable Pipeline from accumulated steps."""
        return Pipeline(steps=self._steps)
