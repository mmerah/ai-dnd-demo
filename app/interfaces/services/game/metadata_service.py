"""Interface for metadata service."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState


class IMetadataService(ABC):
    """Interface for extracting metadata from messages."""

    @abstractmethod
    def extract_npcs_mentioned(self, content: str, known_npcs: list[str]) -> list[str]:
        """Extract NPC names mentioned in content.

        Args:
            content: Message content to analyze
            known_npcs: List of known NPC names

        Returns:
            List of mentioned NPC names
        """
        pass

    @abstractmethod
    def extract_targeted_npcs(self, message: str, game_state: GameState) -> list[str]:
        """Determine which NPCs are being directly addressed in a player message."""

    @abstractmethod
    def get_current_location(self, game_state: GameState) -> str | None:
        """Get the current location

        Args:
            game_state: Current game state

        Returns:
            Current location or None if not available
        """
        pass

    @abstractmethod
    def get_combat_round(self, game_state: GameState) -> int | None:
        """Get the current combat round if in combat.

        Args:
            game_state: Current game state

        Returns:
            Current combat round number or None if not in combat
        """
        pass
