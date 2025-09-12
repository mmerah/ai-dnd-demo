"""Message manager for handling conversation history."""

from datetime import datetime

from app.agents.core.types import AgentType
from app.interfaces.services.game import IMessageManager
from app.models.game_state import GameState, Message, MessageRole


class MessageManager(IMessageManager):
    """Manages conversation history"""

    def add_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType,
        location: str,
        npcs_mentioned: list[str],
        combat_round: int,
        combat_occurrence: int | None = None,
    ) -> Message:
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round if combat_round > 0 else None,
            combat_occurrence=combat_occurrence,
        )

        game_state.add_message(message)
        return message
