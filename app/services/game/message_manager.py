"""Message manager for handling conversation history."""

from datetime import datetime

from app.agents.core.types import AgentType
from app.interfaces.services.game import IMessageManager
from app.models.game_state import GameState, Message, MessageRole


class MessageManager(IMessageManager):
    """Manages conversation history following Single Responsibility Principle.

    Only handles message-related operations on game state.
    """

    def add_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType = AgentType.NARRATIVE,
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> Message:
        """Add a message to conversation history.

        Args:
            game_state: Game state to update
            role: Message role (player/dm)
            content: Message content
            agent_type: Which agent generated this message
            location: Where this message occurred
            npcs_mentioned: NPCs referenced in the message
            combat_round: Combat round if in combat

        Returns:
            Created message
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned if npcs_mentioned is not None else [],
            combat_round=combat_round,
        )

        game_state.add_message(message)
        return message
