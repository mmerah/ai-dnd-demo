"""Auto-continue loop for NPC/monster turns with safety limit."""

import logging
from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.game import ICombatService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


async def run(
    *,
    game_state: GameState,
    combat_service: ICombatService,
    combat_agent: BaseAgent,
    event_bus: IEventBus,
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

        # Check if we should auto-continue for NPC/Monster turns
        if not combat_service.should_auto_continue(game_state):
            logger.info("Not auto-continuing: Player's turn or combat ended")
            break

        # Get current turn for tracking
        current_turn = game_state.combat.get_current_turn()

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
