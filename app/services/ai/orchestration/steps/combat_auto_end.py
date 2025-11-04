"""Step to handle automatic combat end when no enemies remain."""

import logging

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService
from app.interfaces.services.game import IGameService
from app.models.ai_response import StreamEvent
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class CombatAutoEnd:
    """Prompt combat agent to end combat when all enemies are defeated."""

    def __init__(
        self,
        combat_agent: BaseAgent,
        context_service: IContextService,
        event_bus: IEventBus,
        game_service: IGameService,
    ):
        """Initialize with combat agent, context service, event bus, and game service."""
        self.combat_agent = combat_agent
        self.context_service = context_service
        self.event_bus = event_bus
        self.game_service = game_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute combat auto-end sequence."""
        if not ctx.game_state.combat.is_active:
            logger.warning("CombatAutoEnd called but combat is not active")
            return StepResult.continue_with(ctx)

        logger.info("Auto-ending combat: all enemies defeated")

        # Prepare the end combat prompt
        end_combat_prompt = "All enemies have been defeated. End the combat using the end_combat tool."

        # Broadcast system message
        await self.event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=ctx.game_id,
                    content=f"[System: {end_combat_prompt}]",
                    is_complete=True,
                )
            ]
        )

        # Build context for combat agent
        context = self.context_service.build_context(ctx.game_state, AgentType.COMBAT)

        # Execute combat agent to end combat
        events: list[StreamEvent] = []
        async for event in self.combat_agent.process(
            end_combat_prompt,
            ctx.game_state,
            context,
            stream=True,
        ):
            events.append(event)

        logger.debug("Combat agent processed end prompt: %d events", len(events))

        # Reload state after agent execution (end_combat tool sets combat.is_active = False)
        fresh_state = self.game_service.get_game(ctx.game_id)
        updated_ctx = ctx.with_updates(game_state=fresh_state)

        # Add events to context
        updated_ctx = updated_ctx.add_events(events)

        # Return CONTINUE to allow pipeline to reach combat_just_ended transition
        # When used in loops, the loop guard will see combat.is_active=False and exit naturally
        return StepResult.continue_with(updated_ctx)
