"""Step to end dialogue session when appropriate."""

import logging

from app.agents.core.types import AgentType
from app.models.game_state import DialogueSessionMode
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class EndDialogueSessionIfNeeded:
    """End the dialogue session if it's active and in explicit-only mode."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """End dialogue session if needed."""
        session = ctx.game_state.dialogue_session

        # Check if we should end the session
        # Only end if: no NPC targets in this request AND session is active
        should_end = (
            not ctx.flags.npc_targets  # No NPCs targeted in this request
            and session.active  # Session is currently active
            and session.mode is DialogueSessionMode.EXPLICIT_ONLY  # Explicit dialogue mode
        )

        if should_end:
            logger.info("Dialogue session ended, reset to NARRATIVE")

            # Clean up session state
            session.active = False
            session.target_npc_ids = []
            session.started_at = None
            session.last_interaction_at = None

            # Reset active agent to NARRATIVE
            ctx.game_state.active_agent = AgentType.NARRATIVE

        # Always return CONTINUE (this step never halts the pipeline)
        return StepResult.continue_with(ctx)
