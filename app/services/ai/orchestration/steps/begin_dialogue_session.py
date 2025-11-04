"""Step to initialize dialogue session state for NPC interactions."""

import logging
from datetime import datetime

from app.agents.core.types import AgentType
from app.models.game_state import DialogueSessionMode
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BeginDialogueSession:
    """Initialize dialogue session for explicit NPC targeting.

    Sets up the dialogue session state when the user explicitly targets NPCs via
    @mentions. This step configures the session mode to EXPLICIT_ONLY (only
    respond when directly mentioned) and marks the session as active.

    This step requires ctx.flags.npc_targets to be populated by DetectNpcDialogueTargets.
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Begin dialogue session with targeted NPCs.

        Args:
            ctx: Current orchestration context with npc_targets populated

        Returns:
            StepResult with game_state dialogue session updated
        """
        if not ctx.flags.npc_targets:
            # This step should only run when there are NPC targets (guarded by pipeline)
            logger.warning("BeginDialogueSession called without NPC targets")
            return StepResult.continue_with(ctx)

        session = ctx.game_state.dialogue_session
        now = datetime.now()

        # Configure dialogue session (orchestrator lines 197-206)
        session.active = True
        session.mode = DialogueSessionMode.EXPLICIT_ONLY
        session.target_npc_ids = ctx.flags.npc_targets
        session.last_interaction_at = now
        if session.started_at is None:
            session.started_at = now

        # Set active agent to NPC
        ctx.game_state.active_agent = AgentType.NPC

        logger.debug(
            "Started dialogue session with %d NPC(s): %s",
            len(ctx.flags.npc_targets),
            ctx.flags.npc_targets,
        )

        return StepResult.continue_with(ctx)
