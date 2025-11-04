"""Step to build agent context via context service."""

import logging

from app.interfaces.services.ai import IContextService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BuildAgentContext:
    """Build context string for the selected agent using the context service.

    This step uses the context service's strategy pattern to build an appropriate
    context string based on the selected agent type. Each agent type (NARRATIVE,
    COMBAT, NPC) has its own context builder configuration.

    Note: This step requires the SelectAgent step to have run first to set
    selected_agent_type in the context.
    """

    def __init__(self, context_service: IContextService):
        """Initialize the step with required services.

        Args:
            context_service: Service for building agent-specific context
        """
        self.context_service = context_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Build context for the selected agent.

        Args:
            ctx: Current orchestration context with selected_agent_type

        Returns:
            StepResult with context_text updated

        Raises:
            ValueError: If agent type has not been selected yet
        """
        # Ensure agent type is selected (orchestrator line 130)
        agent_type = ctx.require_agent_type()

        logger.info(
            "BuildAgentContext: game_id=%s, agent_type=%s, incoming_context_length=%d",
            ctx.game_id,
            agent_type.value,
            len(ctx.context_text),
        )

        # Build context using context service strategy
        context_text = self.context_service.build_context(ctx.game_state, agent_type)

        logger.info(
            "BuildAgentContext: Built context for agent_type=%s: %d characters",
            agent_type.value,
            len(context_text),
        )

        updated_ctx = ctx.with_updates(context_text=context_text)
        return StepResult.continue_with(updated_ctx)
