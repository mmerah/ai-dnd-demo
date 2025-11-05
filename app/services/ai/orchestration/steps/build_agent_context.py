"""Step to build agent context via context service."""

import logging

from app.interfaces.services.ai import IContextService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BuildAgentContext:
    """Build context string for the selected agent using the context service."""

    def __init__(self, context_service: IContextService):
        """Initialize with context service."""
        self.context_service = context_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Build context for the selected agent."""
        # Ensure agent type is selected
        agent_type = ctx.require_agent_type()

        # Build context using context service strategy
        context_text = self.context_service.build_context(ctx.game_state, agent_type)

        logger.debug("Built %s context: %d characters", agent_type.value, len(context_text))

        updated_ctx = ctx.with_updates(context_text=context_text)
        return StepResult.continue_with(updated_ctx)
