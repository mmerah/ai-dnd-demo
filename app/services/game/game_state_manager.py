"""Game state manager for managing active games in memory."""

from app.interfaces.services.game import IGameStateManager
from app.models.game_state import GameState


class GameStateManager(IGameStateManager):
    """Manages active game states in memory"""

    def __init__(self) -> None:
        self._active_games: dict[str, GameState] = {}

    def store_game(self, game_state: GameState) -> None:
        self._active_games[game_state.game_id] = game_state

    def get_game(self, game_id: str) -> GameState | None:
        return self._active_games.get(game_id)

    def remove_game(self, game_id: str) -> None:
        self._active_games.pop(game_id, None)
