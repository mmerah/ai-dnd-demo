"""Broadcast initial combat prompt step."""

import logging

from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class BroadcastInitialPrompt:
    """Broadcast the initial combat prompt as a system message."""

    def __init__(self, event_bus: IEventBus) -> None:
        """Initialize with event bus."""
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Broadcast the initial combat prompt."""
        if not ctx.current_prompt:
            logger.warning("No current_prompt to broadcast")
            return StepResult.continue_with(ctx)

        # Broadcast as system message
        await self.event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=ctx.game_id,
                    content=f"[Combat System: {ctx.current_prompt}]",
                    is_complete=True,
                )
            ]
        )

        logger.debug("Broadcast initial combat prompt: '%s...'", ctx.current_prompt[:80])

        return StepResult.continue_with(ctx)
