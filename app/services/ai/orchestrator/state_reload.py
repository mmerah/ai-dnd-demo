"""State reload utility for orchestrator checkpoints."""

from app.interfaces.services.game import IGameService
from app.models.game_state import GameState


def reload(game_service: IGameService, game_state: GameState) -> GameState:
    """Reload and return latest in-memory state for the game."""
    reloaded = game_service.get_game(game_state.game_id)
    return reloaded or game_state
