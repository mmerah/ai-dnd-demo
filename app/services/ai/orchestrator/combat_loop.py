"""Auto-continue loop for NPC/monster turns with safety limit."""

import logging
import uuid
from collections.abc import AsyncIterator
from typing import cast

from app.agents.core.base import BaseAgent
from app.agents.npc.base import BaseNPCAgent
from app.events.commands.broadcast_commands import BroadcastCombatSuggestionCommand, BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.interfaces.services.game import ICombatService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


async def _handle_combat_end(
    *,
    game_state: GameState,
    combat_agent: BaseAgent,
    event_bus: IEventBus,
    stream: bool,
) -> AsyncIterator[StreamEvent]:
    """Handle automatic combat end when no enemies remain.

    Args:
        game_state: Current game state
        combat_agent: Agent to narrate combat end
        event_bus: Event bus for broadcasting
        stream: Whether to stream agent responses

    Yields:
        Stream events from combat agent ending combat
    """
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


async def _generate_ally_suggestion(
    *,
    game_state: GameState,
    current_turn: CombatParticipant,
    agent_lifecycle_service: IAgentLifecycleService,
    event_bus: IEventBus,
) -> bool:
    """Generate and broadcast combat suggestion for allied NPC turn.

    Args:
        game_state: Current game state
        current_turn: The ALLY participant whose turn it is
        agent_lifecycle_service: Service for getting NPC agents
        event_bus: Event bus for broadcasting

    Returns:
        True if suggestion was generated and broadcast, False if unable to generate
    """
    logger.info(f"ALLY turn detected for {current_turn.name} - generating combat suggestion")

    # Validate NPC entity type
    if current_turn.entity_type != EntityType.NPC:
        logger.warning(f"ALLY participant is not an NPC (type: {current_turn.entity_type}), skipping suggestion")
        return False

    # Get NPC instance
    npc = game_state.get_npc_by_id(current_turn.entity_id)
    if not npc:
        logger.warning(f"NPC {current_turn.entity_id} not found in game state, cannot generate suggestion")
        return False

    # Get NPC agent and generate suggestion
    npc_agent = cast(BaseNPCAgent, agent_lifecycle_service.get_npc_agent(game_state, npc))
    npc_agent.prepare_for_npc(npc)

    suggestion_prompt = (
        f"You are {npc.display_name}. It is your turn in combat. "
        f"What combat action do you want to take? Describe it briefly in one sentence from your perspective. "
        f"Consider the current combat situation and your abilities."
    )
    logger.debug(f"Prompting {npc.display_name} for combat suggestion")

    # Collect NPC response
    suggestion_text = ""
    async for event in npc_agent.process(suggestion_prompt, game_state, stream=False):
        if event.type == StreamEventType.COMPLETE and isinstance(event.content, NarrativeResponse):
            suggestion_text = event.content.narrative or ""
            break

    # Use default if no suggestion generated
    if not suggestion_text:
        logger.warning(
            f"No suggestion generated for {npc.display_name} (NPC agent returned empty response). "
            f"Using default action. NPC ID: {npc.instance_id}"
        )
        suggestion_text = "I'll attack the nearest enemy."

    # Broadcast suggestion
    suggestion_id = str(uuid.uuid4())
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
    return True


async def _handle_auto_continue_turn(
    *,
    game_state: GameState,
    combat_service: ICombatService,
    combat_agent: BaseAgent,
    event_bus: IEventBus,
    last_prompted_entity_id: str | None,
    last_prompted_round: int,
    iterations: int,
    stream: bool,
) -> AsyncIterator[StreamEvent]:
    """Handle auto-continue for NPC/Monster turns.

    Args:
        game_state: Current game state
        combat_service: Combat service for prompt generation
        combat_agent: Agent to narrate combat actions
        event_bus: Event bus for broadcasting
        last_prompted_entity_id: Last entity prompted (for duplicate detection)
        last_prompted_round: Last round prompted (for duplicate detection)
        iterations: Current iteration count
        stream: Whether to stream agent responses

    Yields:
        Stream events from combat agent processing the turn
    """
    # Generate prompt with tracking parameters
    auto_prompt = combat_service.generate_combat_prompt(
        game_state, last_entity_id=last_prompted_entity_id, last_round=last_prompted_round
    )
    if not auto_prompt:
        return

    logger.info("Auto-continuing combat (iteration %d)", iterations)

    # Broadcast the auto-prompt
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
    last_prompted_entity_id: str | None = None
    last_prompted_round: int = 0

    while iterations < max_iterations:
        iterations += 1

        # Check if combat should end
        if combat_service.should_auto_end_combat(game_state):
            async for event in _handle_combat_end(
                game_state=game_state, combat_agent=combat_agent, event_bus=event_bus, stream=stream
            ):
                yield event
            break

        # Check if current turn is an ALLY - generate suggestion instead of auto-continuing
        current_turn = game_state.combat.get_current_turn()
        if current_turn and current_turn.faction == CombatFaction.ALLY:
            _ = await _generate_ally_suggestion(
                game_state=game_state,
                current_turn=current_turn,
                agent_lifecycle_service=agent_lifecycle_service,
                event_bus=event_bus,
            )
            # Don't auto-continue - wait for player decision
            break

        # Check if we should auto-continue for NPC/Monster turns
        if not combat_service.should_auto_continue(game_state):
            logger.info("Not auto-continuing: Player's turn or combat ended")
            break

        # Handle auto-continue turn
        async for event in _handle_auto_continue_turn(
            game_state=game_state,
            combat_service=combat_service,
            combat_agent=combat_agent,
            event_bus=event_bus,
            last_prompted_entity_id=last_prompted_entity_id,
            last_prompted_round=last_prompted_round,
            iterations=iterations,
            stream=stream,
        ):
            yield event

        # Update tracking state after processing the turn
        if current_turn:
            last_prompted_entity_id = current_turn.entity_id
            last_prompted_round = game_state.combat.round_number

    else:
        # Loop exhausted (no break) -> safety cap reached
        logger.warning("Combat auto-continuation hit safety limit of %d iterations", max_iterations)
