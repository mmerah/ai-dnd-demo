"""Agent transition handling: summaries and broadcasts."""

import logging
from datetime import datetime

from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.models.game_state import GameState, Message, MessageRole

logger = logging.getLogger(__name__)


async def handle_transition(
    game_state: GameState,
    from_type: AgentType,
    to_type: AgentType,
    summarizer_agent: ISummarizerAgent,
    event_bus: IEventBus,
) -> None:
    """Handle context summarization when switching agents.

    Adds the summary as a DM message to conversation history for cleaner context
    and broadcasts a short summary to the frontend.
    """
    try:
        summary: str | None = None
        if to_type == AgentType.COMBAT:
            summary = await summarizer_agent.summarize_for_combat(game_state)
            logger.info("Combat transition summary generated")
        elif to_type == AgentType.NARRATIVE:
            summary = await summarizer_agent.summarize_combat_end(game_state)
            logger.info("Narrative transition summary generated")
        else:
            logger.warning("Unsupported agent transition: %s -> %s", from_type, to_type)
            return

        if not summary:
            return

        # Add summary as a DM message to conversation history
        summary_message = Message(
            role=MessageRole.DM,
            content=f"[Summary: {summary}]",
            timestamp=datetime.now(),
            agent_type=to_type,
            combat_round=game_state.combat.round_number if game_state.combat.is_active else None,
            combat_occurrence=game_state.combat.combat_occurrence if game_state.combat.is_active else None,
        )
        game_state.conversation_history.append(summary_message)

        # Also broadcast the summary to frontend as narrative
        await event_bus.submit_and_wait(
            [
                BroadcastNarrativeCommand(
                    game_id=game_state.game_id,
                    content=f"\n*[{summary}]*\n",
                    is_complete=True,
                )
            ]
        )
        logger.info("Added and broadcast transition summary for %s agent", to_type.value)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error during agent transition summarization: %s", exc)
