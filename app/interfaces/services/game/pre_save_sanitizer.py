"""Interface for pre save sanitizer."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState


class IPreSaveSanitizer(ABC):
    """Interface for sanitizing game state prior to persistence."""

    @abstractmethod
    def sanitize(self, game_state: GameState) -> None:
        """Sanitize game state before saving.

        Ensures consistent state by:
        - Removing dead entities from locations
        - Cleaning up invalid references
        - Normalizing data structures

        Args:
            game_state: Game state to sanitize (modified in-place)
        """
        pass
