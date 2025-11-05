"""Step to execute the selected agent with enriched context."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ExecuteAgent:
    """Execute the selected agent with user message and enriched context."""

    def __init__(
        self,
        narrative_agent: BaseAgent,
        combat_agent: BaseAgent,
    ):
        """Initialize with narrative and combat agents."""
        self.narrative_agent = narrative_agent
        self.combat_agent = combat_agent

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute the selected agent with enriched context."""
        agent_type = ctx.require_agent_type()
        agent = self.combat_agent if agent_type == AgentType.COMBAT else self.narrative_agent

        logger.info("Executing %s agent (context_length=%d)", agent_type.value, len(ctx.context_text))

        # Process with selected agent and collect events
        events: list[StreamEvent] = []
        async for event in agent.process(
            ctx.user_message,
            ctx.game_state,
            ctx.context_text,
            stream=True,
        ):
            events.append(event)

        logger.info("%s agent completed: %d events", agent_type.value, len(events))

        updated_ctx = ctx.add_events(events)
        return StepResult.continue_with(updated_ctx)
