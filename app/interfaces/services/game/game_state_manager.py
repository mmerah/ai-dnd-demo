"""Interface for game state manager."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState


class IGameStateManager(ABC):
    """Interface for managing active game states in memory."""

    @abstractmethod
    def store_game(self, game_state: GameState) -> None:
        """Store a game state in memory.

        Args:
            game_state: Game state to store
        """
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState | None:
        """Get a game state from memory.

        Args:
            game_id: ID of the game

        Returns:
            Game state or None if not found
        """
        pass

    @abstractmethod
    def remove_game(self, game_id: str) -> None:
        """Remove a game state from memory.

        Args:
            game_id: ID of the game to remove
        """
        pass
