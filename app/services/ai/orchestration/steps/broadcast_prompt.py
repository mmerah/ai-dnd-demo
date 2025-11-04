"""Broadcast combat prompt step for combat loop."""

import logging

from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BroadcastPrompt:
    """Broadcast the combat prompt during combat loop auto-continuation."""

    def __init__(self, event_bus: IEventBus) -> None:
        """Initialize with event bus."""
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Broadcast the combat prompt for auto-continuation."""
        if not ctx.current_prompt:
            logger.warning("No current_prompt to broadcast")
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

        logger.debug("Broadcast combat prompt: '%s...'", ctx.current_prompt[:80])

        return StepResult.continue_with(ctx)
