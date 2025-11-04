"""Step protocol and result types for orchestration pipeline."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.services.ai.orchestration.context import OrchestrationContext


class OrchestrationOutcome(str, Enum):
    """Outcome of executing a pipeline step.

    Determines how the pipeline should proceed after a step completes.
    """

    CONTINUE = "continue"
    """Continue to the next step in the pipeline."""

    HALT = "halt"
    """Stop pipeline execution immediately (e.g., after NPC dialogue)."""

    BRANCH = "branch"
    """Reserved for future use (conditional branching logic)."""


@dataclass(frozen=True)
class StepResult:
    """Result returned by a pipeline step.

    Immutable result containing the outcome, updated context, and optional reason.

    Note: Use factory methods (continue_with/halt/branch) rather than direct
    construction to ensure proper reason handling:
    - CONTINUE: No reason needed
    - HALT/BRANCH: Reason required for debugging and observability
    """

    outcome: OrchestrationOutcome
    """How the pipeline should proceed."""

    context: OrchestrationContext
    """Updated orchestration context (may be same or modified)."""

    reason: str | None = None
    """Optional explanation for the outcome (useful for HALT/BRANCH)."""

    @staticmethod
    def continue_with(context: OrchestrationContext) -> "StepResult":
        """Create a CONTINUE result with updated context.

        Args:
            context: Updated orchestration context

        Returns:
            StepResult with CONTINUE outcome
        """
        return StepResult(outcome=OrchestrationOutcome.CONTINUE, context=context)

    @staticmethod
    def halt(context: OrchestrationContext, reason: str) -> "StepResult":
        """Create a HALT result to stop pipeline execution.

        Args:
            context: Final orchestration context
            reason: Explanation for halting (e.g., "NPC dialogue completed")

        Returns:
            StepResult with HALT outcome
        """
        return StepResult(outcome=OrchestrationOutcome.HALT, context=context, reason=reason)

    @staticmethod
    def branch(context: OrchestrationContext, reason: str) -> "StepResult":
        """Create a BRANCH result for conditional execution (future use).

        Args:
            context: Updated orchestration context
            reason: Explanation for branching

        Returns:
            StepResult with BRANCH outcome
        """
        return StepResult(outcome=OrchestrationOutcome.BRANCH, context=context, reason=reason)


class Step(Protocol):
    """Protocol for orchestration pipeline steps.

    Each step is a small, testable unit that performs one orchestration concern.
    Steps receive an OrchestrationContext, perform their logic, and return a
    StepResult with an updated context.

    Steps should be:
    - Pure or mostly pure (side effects through event bus)
    - Small and focused (single responsibility)
    - Type-safe and well-documented
    - Independently testable with mocks

    Example:
        ```python
        class SelectAgent:
            def __init__(self, agent_router: IAgentRouter):
                self.agent_router = agent_router

            async def run(self, ctx: OrchestrationContext) -> StepResult:
                agent_type = self.agent_router.select(ctx.game_state)
                updated_ctx = ctx.with_updates(selected_agent_type=agent_type)
                return StepResult.continue_with(updated_ctx)
        ```
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the step with the given context.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult containing outcome and updated context

        Raises:
            ValueError: If required context fields are missing
            Other exceptions: Step-specific errors (should be caught by pipeline)
        """
        ...
