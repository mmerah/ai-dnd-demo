"""Step to initialize dialogue session state for NPC interactions."""

import logging
from datetime import datetime

from app.agents.core.types import AgentType
from app.models.game_state import DialogueSessionMode
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BeginDialogueSession:
    """Initialize dialogue session for explicit NPC targeting."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Begin dialogue session with targeted NPCs."""
        if not ctx.flags.npc_targets:
            # This step should only run when there are NPC targets (guarded by pipeline)
            logger.warning("BeginDialogueSession called without NPC targets")
            return StepResult.continue_with(ctx)

        session = ctx.game_state.dialogue_session
        now = datetime.now()

        # Configure dialogue session
        session.active = True
        session.mode = DialogueSessionMode.EXPLICIT_ONLY
        session.target_npc_ids = ctx.flags.npc_targets
        session.last_interaction_at = now
        if session.started_at is None:
            session.started_at = now

        # Set active agent to NPC
        ctx.game_state.active_agent = AgentType.NPC

        logger.info("Dialogue session started with %d NPC(s)", len(ctx.flags.npc_targets))

        return StepResult.continue_with(ctx)
