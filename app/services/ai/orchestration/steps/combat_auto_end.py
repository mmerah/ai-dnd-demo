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
    """Prompt combat agent to end combat when all enemies are defeated.

    This step is part of the combat loop decomposition (Phase 5.5). It handles
    the auto-end path from combat_loop.py:_handle_combat_end (lines 23-60).

    When no active enemies remain, this step:
    1. Broadcasts a system message
    2. Prompts the combat agent to call end_combat tool
    3. Collects events from agent execution
    4. Reloads state (combat.is_active becomes False)
    5. Returns CONTINUE to allow pipeline to reach combat_just_ended transition

    When used in loops, the loop guard will check combat.is_active=False and
    exit naturally on the next iteration.
    """

    def __init__(
        self,
        combat_agent: BaseAgent,
        context_service: IContextService,
        event_bus: IEventBus,
        game_service: IGameService,
    ):
        """Initialize the step with required dependencies.

        Args:
            combat_agent: Combat agent to narrate combat end
            context_service: Service for building agent context
            event_bus: Event bus for broadcasting system messages
            game_service: Service for reloading game state
        """
        self.combat_agent = combat_agent
        self.context_service = context_service
        self.event_bus = event_bus
        self.game_service = game_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute combat auto-end sequence.

        Prompts combat agent to end combat using the end_combat tool.
        This replicates combat_loop.py:_handle_combat_end behavior.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with CONTINUE outcome and events from combat agent.
            State is reloaded with combat.is_active=False, allowing subsequent
            guards and the combat_just_ended transition to trigger.
        """
        if not ctx.game_state.combat.is_active:
            logger.warning("CombatAutoEnd called but combat is not active")
            return StepResult.continue_with(ctx)

        logger.info("CombatAutoEnd: No active enemies remain - prompting combat agent to end combat")

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

        logger.info(
            "CombatAutoEnd: Combat agent processed end combat prompt, %d events generated",
            len(events),
        )

        # Reload state after agent execution (end_combat tool sets combat.is_active = False)
        fresh_state = self.game_service.get_game(ctx.game_id)
        updated_ctx = ctx.with_updates(game_state=fresh_state)

        # Add events to context
        updated_ctx = updated_ctx.add_events(events)

        # Return CONTINUE to allow pipeline to reach combat_just_ended transition
        # When used in loops, the loop guard will see combat.is_active=False and exit naturally
        return StepResult.continue_with(updated_ctx)
