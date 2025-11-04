"""Step to execute the selected agent with enriched context."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ExecuteAgent:
    """Execute the selected agent with the user message and enriched context.

    This step delegates to the appropriate agent (narrative or combat) based on
    the selected_agent_type. It passes the user_message, game_state, and
    context_text (which may have been enriched with tool suggestions).

    The step collects all stream events from the agent for observability and
    potential downstream processing.
    """

    def __init__(
        self,
        narrative_agent: BaseAgent,
        combat_agent: BaseAgent,
    ):
        """Initialize the step with agents.

        Args:
            narrative_agent: Agent for story progression
            combat_agent: Agent for tactical combat
        """
        self.narrative_agent = narrative_agent
        self.combat_agent = combat_agent

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the selected agent with enriched context.

        Args:
            ctx: Current orchestration context with agent type, message, and context

        Returns:
            StepResult with events accumulated from agent execution

        Raises:
            ValueError: If agent type has not been selected yet
        """
        # Ensure agent type is selected
        agent_type = ctx.require_agent_type()

        # Select the appropriate agent (orchestrator line 127)
        agent = self.combat_agent if agent_type == AgentType.COMBAT else self.narrative_agent

        logger.info(
            "ExecuteAgent: game_id=%s, agent_type=%s, context_length=%d, user_message_preview='%s...'",
            ctx.game_id,
            agent_type.value,
            len(ctx.context_text),
            ctx.user_message[:50],
        )

        # Process with selected agent (orchestrator lines 155-156)
        # Always stream=True to collect all events
        events: list[StreamEvent] = []
        async for event in agent.process(
            ctx.user_message,
            ctx.game_state,
            ctx.context_text,
            stream=True,
        ):
            events.append(event)

        logger.info(
            "ExecuteAgent: Completed for %s agent: %d events generated",
            agent_type.value,
            len(events),
        )

        # Update context with accumulated events
        updated_ctx = ctx.add_events(events)
        return StepResult.continue_with(updated_ctx)
