"""Interface for game service."""

from abc import ABC, abstractmethod

from app.models.character import CharacterSheet
from app.models.game_state import GameState


class IGameService(ABC):
    """Interface for managing game state."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
        content_packs: list[str] | None = None,
    ) -> GameState:
        """Initialize a new game state.

        Creates a new game with the provided character and scenario,
        stores it in memory, and saves it to disk.

        Args:
            character: The player's character sheet
            scenario_id: Scenario to load
            content_packs: Additional content packs to use (merged with scenario packs)

        Returns:
            Initialized GameState object
        """
        pass

    @abstractmethod
    def save_game(self, game_state: GameState) -> str:
        """Save the game state and return the save path as a string.

        Returns str (stringified Path) for consistency with other API methods
        that return strings for paths, while ISaveManager returns Path objects
        for internal use. This allows the service layer to remain decoupled
        from specific path implementations.
        """
        pass

    @abstractmethod
    def load_game(self, game_id: str) -> GameState:
        """Load game state from disk.

        Args:
            game_id: ID of the game to load

        Returns:
            Loaded GameState object

        Raises:
            FileNotFoundError: If save file doesn't exist
            ValueError: If save file is corrupted
        """
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState:
        """Get active game state from memory or load from disk.

        First checks in-memory cache, then attempts to load from disk
        if not found.

        Args:
            game_id: ID of the game

        Returns:
            GameState object

        Raises:
            FileNotFoundError: If game doesn't exist
        """
        pass

    @abstractmethod
    def list_saved_games(self) -> list[GameState]:
        """List all saved games.

        Returns:
            List of GameState objects for all saved games
        """
        pass

    @abstractmethod
    def remove_game(self, game_id: str) -> None:
        """Remove a game from memory and disk.

        Args:
            game_id: ID of the game to remove
        """
        pass
