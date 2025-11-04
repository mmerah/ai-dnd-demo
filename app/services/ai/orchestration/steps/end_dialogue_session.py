"""Step to end dialogue session when appropriate."""

import logging

from app.agents.core.types import AgentType
from app.models.game_state import DialogueSessionMode
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class EndDialogueSessionIfNeeded:
    """End the dialogue session if it's active and in explicit-only mode.

    This step ensures that after NPC dialogue completes, the game state is
    properly cleaned up and the active agent is reset to NARRATIVE.

    This replicates the behavior of the legacy orchestrator's
    _maybe_end_dialogue_session() method (lines 238-246).

    The step only runs when:
    - No NPC targets in current request (dialogue has ended)
    - Dialogue session is active
    - Mode is EXPLICIT_ONLY (targeted NPC dialogue, not ambient)

    When these conditions are met, the step:
    - Deactivates the dialogue session
    - Clears target NPC IDs
    - Resets timestamps
    - Sets active_agent back to NARRATIVE
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """End dialogue session if needed.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with CONTINUE outcome (state may be modified)
        """
        session = ctx.game_state.dialogue_session

        # Check if we should end the session
        # Only end if: no NPC targets in this request AND session is active
        should_end = (
            not ctx.flags.npc_targets  # No NPCs targeted in this request
            and session.active  # Session is currently active
            and session.mode is DialogueSessionMode.EXPLICIT_ONLY  # Explicit dialogue mode
        )

        if should_end:
            logger.info(
                "EndDialogueSessionIfNeeded: Ending explicit dialogue session for game %s",
                ctx.game_id,
            )

            # Clean up session state (orchestrator lines 242-246)
            session.active = False
            session.target_npc_ids = []
            session.started_at = None
            session.last_interaction_at = None

            # Reset active agent to NARRATIVE (orchestrator line 246)
            ctx.game_state.active_agent = AgentType.NARRATIVE

            logger.info("EndDialogueSessionIfNeeded: Session ended, active_agent reset to NARRATIVE")
        else:
            logger.debug(
                "EndDialogueSessionIfNeeded: No action needed (npc_targets=%s, session.active=%s, mode=%s)",
                bool(ctx.flags.npc_targets),
                session.active,
                session.mode.value if session.mode else None,
            )

        # Always return CONTINUE (this step never halts the pipeline)
        return StepResult.continue_with(ctx)
