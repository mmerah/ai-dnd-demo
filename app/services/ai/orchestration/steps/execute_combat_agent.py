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
    """Execute the combat agent with the current prompt.

    This step:
    1. Builds combat context via context_service
    2. Executes combat_agent.process() with ctx.current_prompt
    3. Collects events in ctx.events

    Used during combat auto-continuation and initial combat execution.
    """

    def __init__(
        self,
        combat_agent: BaseAgent,
        context_service: IContextService,
    ) -> None:
        """Initialize the step with combat agent and context service.

        Args:
            combat_agent: Combat agent for tactical combat
            context_service: Service for building agent context
        """
        self.combat_agent = combat_agent
        self.context_service = context_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the combat agent.

        Args:
            ctx: Current orchestration context with current_prompt set

        Returns:
            StepResult with events accumulated from agent execution
        """
        if not ctx.current_prompt:
            logger.warning("No current_prompt for combat agent (game_id=%s)", ctx.game_id)
            return StepResult.continue_with(ctx)

        # Build combat context
        combat_context = self.context_service.build_context(
            ctx.game_state,
            AgentType.COMBAT,
        )

        logger.info(
            "Executing combat agent: prompt='%s...', context_length=%d (game_id=%s)",
            ctx.current_prompt[:80],
            len(combat_context),
            ctx.game_id,
        )

        # Execute combat agent with prompt
        events: list[StreamEvent] = []
        async for event in self.combat_agent.process(
            ctx.current_prompt,
            ctx.game_state,
            combat_context,
            stream=True,
        ):
            events.append(event)

        logger.info(
            "Combat agent execution completed: %d events generated (game_id=%s)",
            len(events),
            ctx.game_id,
        )

        # Update context with accumulated events
        updated_ctx = ctx.add_events(events)
        return StepResult.continue_with(updated_ctx)
