"""Service for generating ally NPC actions and suggestions.

This service handles ally NPC combat suggestions and can be extended for
narrative-mode ally dialogue, proactive suggestions, and other ally interactions.
"""

import logging
import uuid
from typing import cast

from app.agents.npc.base import BaseNPCAgent
from app.events.commands.broadcast_commands import BroadcastCombatSuggestionCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IAllyActionService
from app.models.ai_response import NarrativeResponse, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class AllyActionService(IAllyActionService):
    """Service for generating ally NPC actions and suggestions.

    Responsibilities:
    - Generate combat suggestions for allied NPCs during their turn
    - Future: Generate proactive ally dialogue during narrative gameplay
    - Future: Handle ally reactions and interjections
    """

    def __init__(
        self,
        agent_lifecycle_service: IAgentLifecycleService,
        event_bus: IEventBus,
    ):
        """Initialize with agent lifecycle service and event bus.

        Args:
            agent_lifecycle_service: Service for managing NPC agent instances
            event_bus: Event bus for broadcasting suggestions via SSE
        """
        self.agent_lifecycle_service = agent_lifecycle_service
        self.event_bus = event_bus

    async def generate_combat_suggestion(self, game_state: GameState) -> None:
        # Validate combat state
        if not game_state.combat.is_active:
            raise ValueError("Cannot generate ally suggestion - combat is not active")

        current_turn = game_state.combat.get_current_turn()
        if not current_turn:
            raise ValueError("Cannot generate ally suggestion - no current turn")

        # Validate it's an ally NPC turn
        if current_turn.faction != CombatFaction.ALLY:
            raise ValueError(
                f"Cannot generate ally suggestion - current turn is {current_turn.faction.value}, not ALLY"
            )

        if current_turn.entity_type != EntityType.NPC:
            raise ValueError(
                f"Cannot generate ally suggestion - current turn entity type is {current_turn.entity_type.value}, not NPC"
            )

        logger.info("Generating combat suggestion for ally: %s (game_id=%s)", current_turn.name, game_state.game_id)

        # Get NPC instance
        npc = game_state.get_npc_by_id(current_turn.entity_id)
        if not npc:
            raise ValueError(f"Allied NPC {current_turn.entity_id} not found in game state")

        # Validate NPC is in party
        if not game_state.party.has_member(npc.instance_id):
            raise ValueError(
                f"NPC {npc.display_name} ({npc.instance_id}) has ALLY faction in combat " f"but is not in the party"
            )

        # Get NPC agent and generate suggestion
        npc_agent = cast(
            BaseNPCAgent,
            self.agent_lifecycle_service.get_npc_agent(game_state, npc),
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
            game_state,
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

        # Broadcast suggestion via event bus
        suggestion_id = str(uuid.uuid4())
        await self.event_bus.submit_and_wait(
            [
                BroadcastCombatSuggestionCommand(
                    game_id=game_state.game_id,
                    suggestion_id=suggestion_id,
                    npc_id=npc.instance_id,
                    npc_name=npc.display_name,
                    action_text=suggestion_text,
                )
            ]
        )

        logger.info(
            "Combat suggestion generated and broadcast for %s: %s",
            npc.display_name,
            suggestion_text[:80],
        )
