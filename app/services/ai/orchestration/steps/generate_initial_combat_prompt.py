"""Generate initial combat prompt step for combat start."""

import logging

from app.interfaces.services.game import ICombatService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class GenerateInitialCombatPrompt:
    """Generate the initial combat prompt when combat starts."""

    def __init__(self, combat_service: ICombatService) -> None:
        """Initialize with combat service."""
        self.combat_service = combat_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Generate the initial combat prompt."""
        # Generate initial prompt without duplicate detection
        prompt = self.combat_service.generate_combat_prompt(ctx.game_state)

        logger.debug("Initial combat prompt: '%s...'", prompt[:80] if prompt else "(empty)")

        # Store prompt in context for broadcasting
        updated_ctx = ctx.with_updates(current_prompt=prompt)
        return StepResult.continue_with(updated_ctx)
