"""Step to execute NPC dialogue interactions."""

import logging
from datetime import datetime
from typing import cast

from app.agents.core.types import AgentType
from app.agents.npc.base import BaseNPCAgent
from app.interfaces.services.ai import IAgentLifecycleService
from app.interfaces.services.game import IConversationService
from app.models.ai_response import StreamEvent
from app.models.game_state import MessageRole
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ExecuteNpcDialogue:
    """Execute dialogue with targeted NPCs and return HALT outcome.

    This step processes the user message with each targeted NPC agent in sequence.
    NPC agents build their own context internally (including persona), so this step
    passes an empty context string.

    After all NPCs respond, this step returns a HALT outcome to stop the pipeline,
    as NPC dialogue is a terminal operation that doesn't continue to other agents.
    """

    def __init__(
        self,
        agent_lifecycle_service: IAgentLifecycleService,
        conversation_service: IConversationService,
    ):
        """Initialize the step with required services.

        Args:
            agent_lifecycle_service: Service for managing NPC agent lifecycle
            conversation_service: Service for recording conversation messages
        """
        self.agent_lifecycle_service = agent_lifecycle_service
        self.conversation_service = conversation_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute dialogue with each targeted NPC.

        Args:
            ctx: Current orchestration context with npc_targets populated

        Returns:
            StepResult with HALT outcome and accumulated NPC response events
        """
        if not ctx.flags.npc_targets:
            logger.warning("ExecuteNpcDialogue called without NPC targets")
            return StepResult.halt(ctx, "No NPC targets to process")

        # Record player message (orchestrator lines 208-213)
        self.conversation_service.record_message(
            ctx.game_state,
            MessageRole.PLAYER,
            ctx.user_message,
            agent_type=AgentType.NPC,
        )

        # Process each targeted NPC (orchestrator lines 215-225)
        accumulated_events: list[StreamEvent] = []

        for npc_id in ctx.flags.npc_targets:
            npc = ctx.game_state.get_npc_by_id(npc_id)
            if npc is None:
                error_msg = f"NPC with id '{npc_id}' not found"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Get NPC agent from lifecycle service
            agent = cast(
                BaseNPCAgent,
                self.agent_lifecycle_service.get_npc_agent(ctx.game_state, npc),
            )
            agent.prepare_for_npc(npc)

            # NPC agents build their own context internally (includes persona)
            # Pass empty string for context (orchestrator line 223)
            events: list[StreamEvent] = []
            async for event in agent.process(ctx.user_message, ctx.game_state, context="", stream=True):
                events.append(event)

            accumulated_events.extend(events)

            # Update session timestamp (orchestrator line 225)
            ctx.game_state.dialogue_session.last_interaction_at = datetime.now()

        # Update context with accumulated events and return HALT
        updated_ctx = ctx.add_events(accumulated_events)

        logger.debug(
            "Completed NPC dialogue with %d NPC(s), generated %d events",
            len(ctx.flags.npc_targets),
            len(accumulated_events),
        )

        return StepResult.halt(updated_ctx, "NPC dialogue completed")
