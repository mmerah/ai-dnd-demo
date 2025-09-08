"""Game endpoints: new/resume/action/equip/SSE and retrieval."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.tasks import process_ai_and_broadcast
from app.container import container
from app.models.game_state import GameState
from app.models.requests import (
    EquipItemRequest,
    EquipItemResponse,
    NewGameRequest,
    NewGameResponse,
    PlayerActionRequest,
    ResumeGameResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/game/new")
async def create_new_game(request: NewGameRequest) -> NewGameResponse:
    """
    Create a new game session.

    Args:
        request: New game request with character selection and optional premise

    Returns:
        Game ID for the newly created session

    Raises:
        HTTPException: If character not found or game creation fails
    """
    game_service = container.game_service
    character_service = container.character_service

    try:
        character = character_service.get_character(request.character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"Character with ID '{request.character_id}' not found")

        game_state = game_service.initialize_game(
            character=character,
            scenario_id=request.scenario_id,
        )

        game_service.save_game(game_state)
        return NewGameResponse(game_id=game_state.game_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {e!s}") from e


@router.get("/games")
async def list_saved_games() -> list[GameState]:
    """
    List all saved games.

    Returns:
        List of saved game summaries with metadata

    Raises:
        HTTPException: If unable to list games
    """
    game_service = container.game_service
    try:
        return game_service.list_saved_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list saved games: {e!s}") from e


@router.get("/game/{game_id}", response_model=GameState)
async def get_game_state(game_id: str) -> GameState:
    """
    Get the complete game state for a session.

    Args:
        game_id: Unique game identifier

    Returns:
        Complete game state including character, NPCs, location, etc.

    Raises:
        HTTPException: If game not found
    """
    game_service = container.game_service
    try:
        game_state = game_service.load_game(game_id)
        return game_state
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid game data: {e!s}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load game: {e!s}") from e


@router.post("/game/{game_id}/resume", response_model=ResumeGameResponse)
async def resume_game(game_id: str) -> ResumeGameResponse:
    """
    Resume a saved game session.

    Args:
        game_id: Unique game identifier

    Returns:
        Confirmation with game_id

    Raises:
        HTTPException: If game not found
    """
    game_service = container.game_service
    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")
        return ResumeGameResponse(game_id=game_id, status="resumed")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume game: {e!s}") from e


@router.post("/game/{game_id}/action")
async def process_player_action(
    game_id: str,
    request: PlayerActionRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """
    Process a player action and trigger AI response processing.

    Args:
        game_id: Unique game identifier
        request: Player's message/action
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Status acknowledgment

    Raises:
        HTTPException: If game not found
    """
    game_service = container.game_service
    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")
        logger.info(f"Processing action for game {game_id}: {request.message[:50]}...")
        background_tasks.add_task(process_ai_and_broadcast, game_id, request.message)
        return {"status": "action received"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process action: {e!s}") from e


@router.post("/game/{game_id}/equip", response_model=EquipItemResponse)
async def equip_item(game_id: str, request: EquipItemRequest) -> EquipItemResponse:
    """Equip or unequip a single unit of a player's inventory item and recompute derived stats.

    Args:
        game_id: Unique game identifier
        request: EquipItemRequest with item name and equipped flag (applies to exactly one unit)

    Returns:
        EquipItemResponse with updated armor class

    Notes:
        - Supports only one-unit operations per call; bulk equip/unequip is not supported
        - Constraints enforced: at most one shield equipped and at most one body armor equipped at a time
    """
    game_service = container.game_service
    message_service = container.message_service
    try:
        updated_state = game_service.set_item_equipped(game_id, request.item_name, request.equipped)
        await message_service.send_game_update(game_id, updated_state)
        item = next(
            (it for it in updated_state.character.state.inventory if it.name.lower() == request.item_name.lower()),
            None,
        )
        final_name = item.name if item else request.item_name
        eq_item = next(
            (it for it in updated_state.character.state.inventory if it.name.lower() == final_name.lower()),
            None,
        )
        equipped_qty = eq_item.equipped_quantity if eq_item else 0
        return EquipItemResponse(
            game_id=game_id,
            item_name=final_name,
            equipped_quantity=equipped_qty,
            new_armor_class=updated_state.character.state.armor_class,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to equip item: {e!s}") from e


@router.get("/game/{game_id}/sse")
async def game_sse_endpoint(game_id: str) -> EventSourceResponse:
    """
    SSE endpoint for real-time game updates.

    This endpoint maintains a persistent connection for pushing
    game state updates, dice roll results, and other events.

    Args:
        game_id: Unique game identifier

    Returns:
        SSE stream for real-time updates

    Raises:
        HTTPException: If game not found
    """
    game_service = container.game_service
    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        message_service = container.message_service
        scenario_service = container.scenario_service
        scenario = game_state.scenario_instance.sheet
        available_scenarios = scenario_service.list_scenarios()
        return EventSourceResponse(
            message_service.generate_sse_events(
                game_id,
                game_state,
                scenario,
                available_scenarios,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to establish SSE connection: {e!s}") from e
