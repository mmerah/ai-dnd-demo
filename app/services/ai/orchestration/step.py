"""Step protocol and result types for orchestration pipeline."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.services.ai.orchestration.context import OrchestrationContext


class OrchestrationOutcome(str, Enum):
    """Outcome that determines how pipeline proceeds after a step."""

    CONTINUE = "continue"
    """Continue to next step."""

    HALT = "halt"
    """Stop pipeline immediately."""

    BRANCH = "branch"
    """Reserved for future use."""


@dataclass(frozen=True)
class StepResult:
    """Result returned by a pipeline step.

    Use factory methods: continue_with() for CONTINUE, halt() for HALT.
    """

    outcome: OrchestrationOutcome
    """How the pipeline should proceed."""

    context: OrchestrationContext
    """Updated orchestration context."""

    reason: str | None = None
    """Explanation for HALT/BRANCH outcomes."""

    @staticmethod
    def continue_with(context: OrchestrationContext) -> "StepResult":
        """Create a CONTINUE result with updated context."""
        return StepResult(outcome=OrchestrationOutcome.CONTINUE, context=context)

    @staticmethod
    def halt(context: OrchestrationContext, reason: str) -> "StepResult":
        """Create a HALT result to stop pipeline execution."""
        return StepResult(outcome=OrchestrationOutcome.HALT, context=context, reason=reason)

    @staticmethod
    def branch(context: OrchestrationContext, reason: str) -> "StepResult":
        """Create a BRANCH result (reserved for future use)."""
        return StepResult(outcome=OrchestrationOutcome.BRANCH, context=context, reason=reason)


class Step(Protocol):
    """Protocol for orchestration pipeline steps.

    Each step performs one orchestration concern and returns a StepResult with
    updated context. Steps should be small, testable, and use event bus for side effects.
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the step with the given context.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with outcome and updated context
        """
        ...
