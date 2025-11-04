"""Broadcast combat prompt step for combat loop."""

import logging

from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BroadcastPrompt:
    """Broadcast the combat prompt during combat loop auto-continuation.

    This step broadcasts the prompt stored in ctx.current_prompt with
    the "[Auto Combat]" prefix to indicate automatic turn processing.
    """

    def __init__(self, event_bus: IEventBus) -> None:
        """Initialize the step with event bus.

        Args:
            event_bus: Event bus for broadcasting messages
        """
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Broadcast the combat prompt for auto-continuation.

        Args:
            ctx: Current orchestration context with current_prompt set

        Returns:
            StepResult (CONTINUE outcome)
        """
        if not ctx.current_prompt:
            logger.warning("No current_prompt to broadcast (game_id=%s)", ctx.game_id)
            return StepResult.continue_with(ctx)

        # Broadcast with auto combat prefix
        await self.event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=ctx.game_id,
                    content=f"[Auto Combat] {ctx.current_prompt}",
                    is_complete=True,
                )
            ]
        )

        logger.info(
            "Broadcast combat prompt: '%s...' (game_id=%s)",
            ctx.current_prompt[:80],
            ctx.game_id,
        )

        return StepResult.continue_with(ctx)
