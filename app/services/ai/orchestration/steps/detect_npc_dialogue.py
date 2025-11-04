"""Step to detect NPC dialogue targets in user messages."""

import logging

from app.interfaces.services.game import IMetadataService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class DetectNpcDialogueTargets:
    """Detect if user message targets specific NPCs via @mentions.

    This step uses the metadata service to extract NPC targets from the user message
    (e.g., "@Tom hello" would target an NPC named Tom). Detected NPC IDs are stored
    in context.flags.npc_targets for downstream steps to use.

    Only runs when not in combat (combat has different NPC interaction rules).
    """

    def __init__(self, metadata_service: IMetadataService):
        """Initialize the step with required services.

        Args:
            metadata_service: Service for extracting metadata from messages
        """
        self.metadata_service = metadata_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Detect NPC targets in the user message.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with npc_targets flag updated if any NPCs were mentioned
        """
        try:
            targeted_npc_ids = self.metadata_service.extract_targeted_npcs(ctx.user_message, ctx.game_state)

            if targeted_npc_ids:
                logger.debug(
                    "Detected %d NPC target(s): %s",
                    len(targeted_npc_ids),
                    targeted_npc_ids,
                )
                updated_flags = ctx.flags.with_updates(npc_targets=targeted_npc_ids)
                updated_ctx = ctx.with_updates(flags=updated_flags)
                return StepResult.continue_with(updated_ctx)

            return StepResult.continue_with(ctx)

        except ValueError as exc:
            # metadata_service raises ValueError for unknown NPCs
            logger.warning("Failed to resolve targeted NPCs: %s", exc)
            # Re-raise to maintain current behavior (orchestrator line 186-188)
            raise
