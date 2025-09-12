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
        agent_type: AgentType,
        location: str,
        npcs_mentioned: list[str],
        combat_round: int,
        combat_occurrence: int | None = None,
    ) -> Message:
        """Add a message to conversation history.

        Args:
            game_state: Game state to update
            role: Message role (player/dm)
            content: Message content
            agent_type: Which agent generated this message
            location: Where this message occurred
            npcs_mentioned: NPCs referenced in the message
            combat_round: Combat round if in combat (0 if not in combat)

        Returns:
            Created message
        """
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
