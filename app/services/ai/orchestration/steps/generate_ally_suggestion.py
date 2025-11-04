"""Step to generate combat suggestion for allied NPC turns."""

import logging
import uuid
from typing import cast

from app.agents.npc.base import BaseNPCAgent
from app.events.commands.broadcast_commands import BroadcastCombatSuggestionCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.models.ai_response import NarrativeResponse, StreamEventType
from app.models.attributes import EntityType
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class GenerateAllySuggestion:
    """Generate and broadcast combat suggestion for allied NPC turn."""

    def __init__(
        self,
        agent_lifecycle_service: IAgentLifecycleService,
        event_bus: IEventBus,
    ):
        """Initialize with agent lifecycle service and event bus."""
        self.agent_lifecycle_service = agent_lifecycle_service
        self.event_bus = event_bus

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Generate and broadcast combat suggestion for ally NPC."""
        if not ctx.game_state.combat.is_active:
            logger.warning("GenerateAllySuggestion called but combat is not active")
            return StepResult.continue_with(ctx)

        current_turn = ctx.game_state.combat.get_current_turn()
        if not current_turn:
            logger.warning("GenerateAllySuggestion called but no current turn")
            return StepResult.continue_with(ctx)

        logger.info("Generating combat suggestion for ally: %s", current_turn.name)

        # Validate NPC entity type
        if current_turn.entity_type != EntityType.NPC:
            raise ValueError(
                f"Cannot generate combat suggestion for non-NPC entity: {current_turn.name} "
                f"(type: {current_turn.entity_type})"
            )

        # Get NPC instance
        npc = ctx.game_state.get_npc_by_id(current_turn.entity_id)
        if not npc:
            raise ValueError(f"Allied NPC {current_turn.entity_id} not found in game state for combat suggestion")

        # Validate NPC is in party
        if not ctx.game_state.party.has_member(npc.instance_id):
            raise ValueError(
                f"NPC {npc.display_name} ({npc.instance_id}) has ALLY faction in combat " f"but is not in the party"
            )

        # Get NPC agent and generate suggestion
        npc_agent = cast(
            BaseNPCAgent,
            self.agent_lifecycle_service.get_npc_agent(ctx.game_state, npc),
        )
        npc_agent.prepare_for_npc(npc)

        suggestion_prompt = (
            f"You are {npc.display_name}. It is your turn in combat. "
            f"What combat action do you want to take? Describe it briefly in one sentence from your perspective. "
            f"Consider the current combat situation and your abilities."
        )

        # Collect NPC response (NPC agents build their own context internally)
        suggestion_text = ""
        async for event in npc_agent.process(
            suggestion_prompt,
            ctx.game_state,
            context="",
            stream=False,
        ):
            if event.type == StreamEventType.COMPLETE and isinstance(event.content, NarrativeResponse):
                suggestion_text = event.content.narrative or ""
                break

        # Use default if no suggestion generated
        if not suggestion_text:
            logger.warning(
                "No suggestion generated for %s (NPC agent returned empty response). "
                "Using default action. NPC ID: %s",
                npc.display_name,
                npc.instance_id,
            )
            suggestion_text = "I'll attack the nearest enemy."

        # Broadcast suggestion
        suggestion_id = str(uuid.uuid4())
        await self.event_bus.submit_and_wait(
            [
                BroadcastCombatSuggestionCommand(
                    game_id=ctx.game_id,
                    suggestion_id=suggestion_id,
                    npc_id=npc.instance_id,
                    npc_name=npc.display_name,
                    action_text=suggestion_text,
                )
            ]
        )

        logger.debug("Suggestion for %s: %s", npc.display_name, suggestion_text[:80])

        # HALT the loop - we need to wait for player decision
        return StepResult.halt(
            ctx,
            f"Ally NPC {npc.display_name} suggestion generated, waiting for player decision",
        )
