"""
API routes for D&D 5e AI Dungeon Master.
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.tasks import process_ai_and_broadcast
from app.container import container

# Import core models directly instead of duplicate API response models
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.item import ItemDefinition
from app.models.requests import NewGameRequest, NewGameResponse, PlayerActionRequest
from app.models.scenario import Scenario
from app.models.spell import SpellDefinition
from app.models.sse_events import (
    GameUpdateData,
    InitialNarrativeData,
    ScenarioInfoData,
    SSEEvent,
    SSEEventType,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()


# Endpoints
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
    game_service = container.get_game_service()
    character_service = container.get_character_service()

    try:
        # Get the selected character
        character = character_service.get_character(request.character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"Character with ID '{request.character_id}' not found")

        # Initialize game state
        game_state = game_service.initialize_game(
            character=character,
            premise=request.premise,
            scenario_id=request.scenario_id,
        )

        # Don't send initial narrative here - it will be sent when SSE connects
        # to ensure the client receives it

        # Save initial game state
        game_service.save_game(game_state)

        return NewGameResponse(game_id=game_state.game_id)

    except HTTPException:
        raise
    except Exception as e:
        # Fail fast principle - no silent failures
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
    game_service = container.get_game_service()

    try:
        # Service will return list of GameState objects
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
    game_service = container.get_game_service()

    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        return game_state

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load game: {e!s}") from e


@router.post("/game/{game_id}/resume")
async def resume_game(game_id: str) -> dict[str, str]:
    """
    Resume a saved game session.

    Args:
        game_id: Unique game identifier

    Returns:
        Confirmation with game_id

    Raises:
        HTTPException: If game not found
    """
    game_service = container.get_game_service()

    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        # Game successfully loaded and cached in memory
        return {"game_id": game_id, "status": "resumed"}

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
    game_service = container.get_game_service()

    try:
        # Verify game exists
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        # Add the AI processing task to background
        logger.info(f"Processing action for game {game_id}: {request.message[:50]}...")
        background_tasks.add_task(process_ai_and_broadcast, game_id, request.message)

        # Return immediate acknowledgment
        return {"status": "action received"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process action: {e!s}") from e


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
    game_service = container.get_game_service()

    try:
        # Verify game exists
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        async def event_generator() -> AsyncGenerator[dict[str, str], None]:
            scenario_service = container.get_scenario_service()
            broadcast_service = container.get_broadcast_service()

            """Generate SSE events by subscribing to broadcast service."""
            logger.info(f"Client subscribed to SSE for game {game_id}")

            # Send initial narrative
            if game_state.conversation_history:
                initial_event = SSEEvent(
                    event=SSEEventType.INITIAL_NARRATIVE,
                    data=InitialNarrativeData(
                        scenario_title=game_state.scenario_title or "Custom Adventure",
                        narrative=game_state.conversation_history[0].content,
                    ),
                )
                yield initial_event.to_sse_format()

            # Send initial full game state
            initial_game_update_event = SSEEvent(
                event=SSEEventType.GAME_UPDATE,
                data=GameUpdateData(game_state=game_state),
            )
            yield initial_game_update_event.to_sse_format()

            # Send scenario info
            if game_state.scenario_id:
                scenario = scenario_service.get_scenario(game_state.scenario_id)
                scenarios = scenario_service.list_scenarios()
                if scenario:
                    scenario_event = SSEEvent(
                        event=SSEEventType.SCENARIO_INFO,
                        data=ScenarioInfoData(
                            current_scenario=scenario,
                            available_scenarios=scenarios,
                        ),
                    )
                    yield scenario_event.to_sse_format()

            async for event_data in broadcast_service.subscribe(game_id):
                # event_data is already in SSE format from broadcast_service
                if event_data["event"] != "narrative":
                    logger.debug(f"Sending SSE event '{event_data['event']}' to game {game_id}")
                yield event_data

        return EventSourceResponse(event_generator())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to establish SSE connection: {e!s}") from e


@router.get("/scenarios")
async def list_available_scenarios() -> list[Scenario]:
    """
    List all available scenarios.

    Returns:
        List of scenario summaries

    Raises:
        HTTPException: If scenarios cannot be loaded
    """
    scenario_service = container.get_scenario_service()

    try:
        # Return full scenario objects, not summaries
        return scenario_service.list_scenarios()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenarios: {e!s}") from e


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> Scenario:
    """
    Get a specific scenario by ID.

    Args:
        scenario_id: Unique scenario identifier

    Returns:
        Scenario data

    Raises:
        HTTPException: If scenario not found
    """
    scenario_service = container.get_scenario_service()

    try:
        scenario = scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario with ID '{scenario_id}' not found")

        return scenario

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {e!s}") from e


@router.get("/characters", response_model=list[CharacterSheet])
async def list_available_characters() -> list[CharacterSheet]:
    """
    List all available pre-generated characters.

    Returns:
        List of character sheets for selection

    Raises:
        HTTPException: If characters data cannot be loaded
    """
    character_service = container.get_character_service()

    try:
        # Get all characters from the service
        characters = character_service.get_all_characters()
        return characters

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load characters: {e!s}") from e


@router.get("/items/{item_name}")
async def get_item_details(item_name: str) -> ItemDefinition:
    """
    Get detailed information about an item.

    Args:
        item_name: Name of the item

    Returns:
        Item details including description

    Raises:
        HTTPException: If item not found
    """
    data_service = container.get_data_service()

    try:
        item = data_service.get_item(item_name, allow_missing=True)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{item_name}' not found")

        return item

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item details: {e!s}") from e


@router.get("/spells/{spell_name}")
async def get_spell_details(spell_name: str) -> SpellDefinition:
    """
    Get detailed information about a spell.

    Args:
        spell_name: Name of the spell

    Returns:
        Spell details including description

    Raises:
        HTTPException: If spell not found
    """
    data_service = container.get_data_service()

    try:
        spell = data_service.get_spell(spell_name, allow_missing=True)
        if not spell:
            raise HTTPException(status_code=404, detail=f"Spell '{spell_name}' not found")

        return spell

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get spell details: {e!s}") from e
