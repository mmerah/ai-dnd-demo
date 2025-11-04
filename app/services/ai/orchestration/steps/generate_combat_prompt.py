"""Generate combat prompt step with duplicate detection."""

import logging

from app.interfaces.services.game import ICombatService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class GenerateCombatPrompt:
    """Generate combat prompt with duplicate detection tracking.

    This step:
    1. Reads last_prompted_entity_id and last_prompted_round from ctx.flags
    2. Calls combat_service.generate_combat_prompt() with tracking params
    3. Updates flags in returned context with current entity/round
    4. Stores prompt in ctx.current_prompt for broadcasting

    This is used in the combat loop (not for initial prompt).
    """

    def __init__(self, combat_service: ICombatService) -> None:
        """Initialize the step with combat service.

        Args:
            combat_service: Service for generating combat prompts
        """
        self.combat_service = combat_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Generate combat prompt with duplicate detection.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with current_prompt and flags updated in context
        """
        # Read tracking params from flags
        last_entity_id = ctx.flags.last_prompted_entity_id
        last_round = ctx.flags.last_prompted_round

        # Generate prompt with duplicate detection
        prompt = self.combat_service.generate_combat_prompt(
            ctx.game_state,
            last_entity_id=last_entity_id,
            last_round=last_round,
        )

        # Get current turn info for tracking
        current_turn = ctx.game_state.combat.get_current_turn()
        current_entity_id = current_turn.entity_id if current_turn else None
        current_round = ctx.game_state.combat.round_number

        logger.info(
            "Generated combat prompt: entity=%s, round=%d, prompt='%s...' (game_id=%s)",
            current_entity_id or "(none)",
            current_round,
            prompt[:80] if prompt else "(empty)",
            ctx.game_id,
        )

        # Update flags with current tracking info
        updated_flags = ctx.flags.with_updates(
            last_prompted_entity_id=current_entity_id,
            last_prompted_round=current_round,
        )

        # Store prompt and flags in context
        updated_ctx = ctx.with_updates(
            current_prompt=prompt,
            flags=updated_flags,
        )
        return StepResult.continue_with(updated_ctx)
