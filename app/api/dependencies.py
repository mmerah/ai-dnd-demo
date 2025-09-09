"""FastAPI dependencies for common request operations."""

from fastapi import Depends, HTTPException, Path

from app.container import container
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState


def get_game_service() -> IGameService:
    """Get the game service from the dependency container."""
    return container.game_service


async def get_game_state_from_path(
    game_id: str = Path(...), game_service: IGameService = Depends(get_game_service)
) -> GameState:
    """A FastAPI dependency to load a game state by its ID from the path.

    Args:
        game_id: The game ID from the path parameter
        game_service: The game service (injected)

    Returns:
        The loaded GameState

    Raises:
        HTTPException: 404 if game not found, 400 if invalid data
    """
    try:
        game_state = game_service.load_game(game_id)
        return game_state
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid game data: {e!s}") from e
