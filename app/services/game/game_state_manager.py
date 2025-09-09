"""Game state manager for managing active games in memory."""

from app.interfaces.services.game import IGameStateManager
from app.models.game_state import GameState


class GameStateManager(IGameStateManager):
    """Manages active game states in memory following Single Responsibility Principle.

    Only handles in-memory storage and retrieval of game states.
    """

    def __init__(self) -> None:
        """Initialize the game state manager."""
        self._active_games: dict[str, GameState] = {}

    def store_game(self, game_state: GameState) -> None:
        """Store a game state in memory.

        Args:
            game_state: Game state to store
        """
        self._active_games[game_state.game_id] = game_state

    def get_game(self, game_id: str) -> GameState | None:
        """Get a game state from memory.

        Args:
            game_id: ID of the game

        Returns:
            Game state or None if not found
        """
        return self._active_games.get(game_id)

    def remove_game(self, game_id: str) -> None:
        """Remove a game state from memory.

        Args:
            game_id: ID of the game to remove
        """
        self._active_games.pop(game_id, None)
