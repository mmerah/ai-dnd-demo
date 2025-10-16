"""Auto-continue loop for NPC/monster turns with safety limit."""

import logging
import uuid
from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent
from app.events.commands.broadcast_commands import BroadcastCombatSuggestionCommand, BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.interfaces.services.game import ICombatService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


async def run(
    *,
    game_state: GameState,
    combat_service: ICombatService,
    combat_agent: BaseAgent,
    event_bus: IEventBus,
    agent_lifecycle_service: IAgentLifecycleService,
    stream: bool = True,
) -> AsyncIterator[StreamEvent]:
    """Automatically continue combat if it's an NPC/Monster turn and handle auto-end.

    Yields stream events coming from the combat agent as the loop progresses.
    """
    if not game_state.combat.is_active:
        logger.warning("Combat continuation called but combat is not active for game %s", game_state.game_id)
        return

    max_iterations = 50
    iterations = 0

    # State management in the orchestrator
    last_prompted_entity_id: str | None = None
    last_prompted_round: int = 0

    while iterations < max_iterations:
        iterations += 1

        # First check if combat should end (no active enemies)
        if combat_service.should_auto_end_combat(game_state):
            logger.info("No active enemies remain - prompting combat agent to end combat")
            end_combat_prompt = "All enemies have been defeated. End the combat using the end_combat tool."

            # Broadcast the prompt
            await event_bus.submit_and_wait(
                [
                    BroadcastNarrativeCommand(
                        game_id=game_state.game_id,
                        content=f"[System: {end_combat_prompt}]",
                        is_complete=True,
                    )
                ]
            )

            # Process with combat agent to end combat
            async for event in combat_agent.process(end_combat_prompt, game_state, stream=stream):
                yield event
            break

        # Check if current turn is an ALLY - generate suggestion instead of auto-continuing
        current_turn = game_state.combat.get_current_turn()
        if current_turn and current_turn.faction == CombatFaction.ALLY:
            logger.info(f"ALLY turn detected for {current_turn.name} - generating combat suggestion")

            # Get the NPC instance
            if current_turn.entity_type != EntityType.NPC:
                logger.warning(
                    f"ALLY participant is not an NPC (type: {current_turn.entity_type}), skipping suggestion"
                )
                break

            npc = game_state.get_npc_by_id(current_turn.entity_id)
            if not npc:
                logger.warning(f"NPC {current_turn.entity_id} not found in game state, cannot generate suggestion")
                break

            # Get the NPC agent
            npc_agent = agent_lifecycle_service.get_npc_agent(game_state, npc)

            # Generate suggestion prompt
            suggestion_prompt = (
                f"You are {npc.display_name}. It is your turn in combat. "
                f"What combat action do you want to take? Describe it briefly in one sentence from your perspective. "
                f"Consider the current combat situation and your abilities."
            )
            logger.debug(f"Prompting {npc.display_name} for combat suggestion")

            # Collect the NPC's response
            suggestion_text = ""
            async for event in npc_agent.process(suggestion_prompt, game_state, stream=False):
                if event.type == StreamEventType.COMPLETE and isinstance(event.content, NarrativeResponse):
                    suggestion_text = event.content.narrative or ""
                    break

            if not suggestion_text:
                logger.warning(f"No suggestion generated for {npc.display_name}, using default")
                suggestion_text = "I'll attack the nearest enemy."

            # Generate unique suggestion ID
            suggestion_id = str(uuid.uuid4())

            # Broadcast the suggestion via SSE
            await event_bus.submit_and_wait(
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

            logger.info(f"Combat suggestion broadcast for {npc.display_name}: {suggestion_text}")
            # Don't auto-continue - wait for player decision
            break

        # Check if we should auto-continue for NPC/Monster turns
        if not combat_service.should_auto_continue(game_state):
            logger.info("Not auto-continuing: Player's turn or combat ended")
            break

        # Generate prompt with tracking parameters
        auto_prompt = combat_service.generate_combat_prompt(
            game_state, last_entity_id=last_prompted_entity_id, last_round=last_prompted_round
        )
        if not auto_prompt:
            break

        # Update tracking state in orchestrator
        if current_turn:
            last_prompted_entity_id = current_turn.entity_id
            last_prompted_round = game_state.combat.round_number

        logger.info("Auto-continuing combat (iteration %d)", iterations)

        # Broadcast the auto-prompt so it appears in real-time
        await event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=game_state.game_id,
                    content=f"[Auto Combat: {auto_prompt}]",
                    is_complete=True,
                )
            ]
        )

        # Process with combat agent
        async for event in combat_agent.process(auto_prompt, game_state, stream=stream):
            yield event

        # Next iteration will re-evaluate conditions (end or continue)
    else:
        # Loop exhausted (no break) → safety cap reached
        logger.warning("Combat auto-continuation hit safety limit of %d iterations", max_iterations)
