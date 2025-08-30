"""
API routes for D&D 5e AI Dungeon Master.
"""

import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.tasks import process_ai_and_broadcast
from app.container import container
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.requests import NewGameRequest, NewGameResponse, PlayerActionRequest
from app.services.broadcast_service import broadcast_service

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()


# Endpoints
@router.post("/game/new", response_model=NewGameResponse)
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

    try:
        # Load available characters
        characters_path = Path(__file__).parent.parent / "data" / "characters.json"
        if not characters_path.exists():
            raise HTTPException(status_code=500, detail="Characters data not found")

        with open(characters_path) as f:
            characters_data = json.load(f)

        # Find selected character
        character_data = None
        for char in characters_data.get("characters", []):
            if char.get("id") == request.character_id:
                character_data = char
                break

        if not character_data:
            raise HTTPException(status_code=404, detail=f"Character with ID '{request.character_id}' not found")

        # Create character sheet from data
        character = CharacterSheet(**character_data)

        # Initialize game state
        game_state = game_service.initialize_game(
            character=character, premise=request.premise, scenario_id=request.scenario_id
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
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}") from e


@router.get("/games")
async def list_saved_games() -> list[dict[str, str]]:
    """
    List all saved games.

    Returns:
        List of saved game summaries with metadata

    Raises:
        HTTPException: If unable to list games
    """
    game_service = container.get_game_service()

    try:
        saved_games = game_service.list_saved_games()
        return saved_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list saved games: {str(e)}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to load game: {str(e)}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to resume game: {str(e)}") from e


@router.post("/game/{game_id}/action")
async def process_player_action(
    game_id: str, request: PlayerActionRequest, background_tasks: BackgroundTasks
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
        raise HTTPException(status_code=500, detail=f"Failed to process action: {str(e)}") from e


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

            """Generate SSE events by subscribing to broadcast service."""
            logger.info(f"Client subscribed to SSE for game {game_id}")
            subscriber_count = broadcast_service.get_subscriber_count(game_id)
            logger.debug(f"Current subscribers for game {game_id}: {subscriber_count}")

            # Send initial narrative and scenario info when SSE connects
            if game_state.conversation_history:
                yield {
                    "event": "initial_narrative",
                    "data": json.dumps(
                        {
                            "scenario_title": game_state.scenario_title or "Custom Adventure",
                            "narrative": game_state.conversation_history[0].content,
                        }
                    ),
                }

            # Send scenario info if available
            if game_state.scenario_id:
                scenarios = scenario_service.list_scenarios()
                yield {
                    "event": "scenario_info",
                    "data": json.dumps(
                        {
                            "current_scenario": {"id": game_state.scenario_id, "title": game_state.scenario_title},
                            "available_scenarios": scenarios,
                        }
                    ),
                }

            async for event_data in broadcast_service.subscribe(game_id):
                # Format the event for SSE - only log non-narrative events
                if event_data["event"] != "narrative":
                    logger.debug(f"Sending SSE event '{event_data['event']}' to game {game_id}")
                yield {"event": event_data["event"], "data": json.dumps(event_data["data"])}

        return EventSourceResponse(event_generator())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to establish SSE connection: {str(e)}") from e


@router.get("/scenarios")
async def list_available_scenarios() -> list[dict[str, str]]:
    """
    List all available scenarios.

    Returns:
        List of scenario summaries

    Raises:
        HTTPException: If scenarios cannot be loaded
    """
    scenario_service = container.get_scenario_service()

    try:
        scenarios = scenario_service.list_scenarios()
        return scenarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenarios: {str(e)}") from e


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict[str, Any]:
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

        return {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "starting_location": scenario.starting_location,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {str(e)}") from e


@router.get("/characters", response_model=list[CharacterSheet])
async def list_available_characters() -> list[CharacterSheet]:
    """
    List all available pre-generated characters.

    Returns:
        List of character sheets for selection

    Raises:
        HTTPException: If characters data cannot be loaded
    """
    try:
        # Load characters data
        characters_path = Path(__file__).parent.parent / "data" / "characters.json"
        if not characters_path.exists():
            raise HTTPException(status_code=500, detail="Characters data not found")

        with open(characters_path) as f:
            characters_data = json.load(f)

        # Convert to CharacterSheet objects
        characters = [CharacterSheet(**char_data) for char_data in characters_data.get("characters", [])]

        return characters

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load characters: {str(e)}") from e
