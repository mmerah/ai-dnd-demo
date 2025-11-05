"""Step to detect NPC dialogue targets in user messages."""

import logging

from app.interfaces.services.game import IMetadataService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class DetectNpcDialogueTargets:
    """Detect if user message targets specific NPCs via @mentions."""

    def __init__(self, metadata_service: IMetadataService):
        """Initialize with metadata service."""
        self.metadata_service = metadata_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Detect NPC targets in the user message."""
        try:
            targeted_npc_ids = self.metadata_service.extract_targeted_npcs(ctx.user_message, ctx.game_state)

            if targeted_npc_ids:
                logger.info("Detected %d NPC target(s)", len(targeted_npc_ids))
                updated_flags = ctx.flags.with_updates(npc_targets=targeted_npc_ids)
                updated_ctx = ctx.with_updates(flags=updated_flags)
                return StepResult.continue_with(updated_ctx)

            return StepResult.continue_with(ctx)

        except ValueError as exc:
            logger.warning("Failed to resolve targeted NPCs: %s", exc)
            # Re-raise
            raise
