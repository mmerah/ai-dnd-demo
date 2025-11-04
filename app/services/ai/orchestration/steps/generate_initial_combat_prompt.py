"""Generate initial combat prompt step for combat start."""

import logging

from app.interfaces.services.game import ICombatService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class GenerateInitialCombatPrompt:
    """Generate the initial combat prompt when combat starts.

    This step calls combat_service.generate_combat_prompt() without
    duplicate detection tracking (no last_entity_id or last_round).
    The prompt is stored in ctx.current_prompt for the next step to broadcast.
    """

    def __init__(self, combat_service: ICombatService) -> None:
        """Initialize the step with combat service.

        Args:
            combat_service: Service for generating combat prompts
        """
        self.combat_service = combat_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Generate the initial combat prompt.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with current_prompt updated in context
        """
        # Generate initial prompt without duplicate detection
        prompt = self.combat_service.generate_combat_prompt(ctx.game_state)

        logger.info(
            "Generated initial combat prompt: '%s...' (game_id=%s)",
            prompt[:80] if prompt else "(empty)",
            ctx.game_id,
        )

        # Store prompt in context for broadcasting
        updated_ctx = ctx.with_updates(current_prompt=prompt)
        return StepResult.continue_with(updated_ctx)
