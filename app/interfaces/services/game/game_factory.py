"""Interface for game factory."""

from abc import ABC, abstractmethod

from app.models.character import CharacterSheet
from app.models.game_state import GameState


class IGameFactory(ABC):
    """Interface for creating new game instances."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
        content_packs: list[str] | None = None,
    ) -> GameState:
        """Initialize a new game state.

        Args:
            character: The player's character sheet
            scenario_id: Scenario to load
            content_packs: Additional content packs to use (merged with scenario packs)

        Returns:
            Initialized GameState object
        """
        pass
