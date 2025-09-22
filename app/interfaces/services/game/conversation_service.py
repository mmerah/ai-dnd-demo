"""Interface for conversation service."""

from abc import ABC, abstractmethod

from app.agents.core.types import AgentType
from app.models.game_state import GameState, Message, MessageRole


class IConversationService(ABC):
    """Interface for recording narrative messages with metadata and persistence."""

    @abstractmethod
    def record_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType = AgentType.NARRATIVE,
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
    ) -> Message:
        """Add a message to the conversation, auto-extract metadata from game state, and save.

        Metadata (location, NPCs mentioned, combat round) is extracted from the game state.
        Returns the created Message.
        """
        pass

    @abstractmethod
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
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
    ) -> Message:
        """Add a message to conversation history.

        Args:
            game_state: Game state to update
            role: Message role
            content: Message content
            agent_type: Which agent generated this
            location: Where this occurred
            npcs_mentioned: NPCs referenced
            combat_round: Combat round if in combat
            combat_occurrence: Which combat occurrence this message belongs to
            speaker_npc_id: ID of NPC speaker (if applicable)
            speaker_npc_name: Name of NPC speaker (if applicable)

        Returns:
            Created message
        """
        pass
