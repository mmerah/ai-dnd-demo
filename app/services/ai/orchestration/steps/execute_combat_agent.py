"""Execute combat agent step."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ExecuteCombatAgent:
    """Execute the combat agent with the current prompt."""

    def __init__(
        self,
        combat_agent: BaseAgent,
        context_service: IContextService,
    ) -> None:
        """Initialize with combat agent and context service."""
        self.combat_agent = combat_agent
        self.context_service = context_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the combat agent."""
        if not ctx.current_prompt:
            logger.warning("No current_prompt for combat agent")
            return StepResult.continue_with(ctx)

        # Build combat context
        combat_context = self.context_service.build_context(
            ctx.game_state,
            AgentType.COMBAT,
        )

        logger.debug("Executing combat agent: prompt='%s...'", ctx.current_prompt[:80])

        # Execute combat agent with prompt
        events: list[StreamEvent] = []
        async for event in self.combat_agent.process(
            ctx.current_prompt,
            ctx.game_state,
            combat_context,
            stream=True,
        ):
            events.append(event)

        logger.debug("Combat agent completed: %d events", len(events))

        # Update context with accumulated events
        updated_ctx = ctx.add_events(events)
        return StepResult.continue_with(updated_ctx)
