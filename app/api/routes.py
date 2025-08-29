"""
API routes for D&D 5e AI Dungeon Master.
"""

import json
import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.requests import NewGameRequest, NewGameResponse, PlayerActionRequest
from app.services.ai_service import AIService
from app.services.broadcast_service import broadcast_service
from app.services.game_service import GameService
from app.services.message_service import message_service
from app.services.scenario_service import ScenarioService

# TODO: Clean this up. Shouldn't there be a config.py and this kind of thing should not be necessary
# Check if debug mode is enabled via environment variable
DEBUG_MODE = os.getenv("DEBUG_AI", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO

logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logger.info("DEBUG MODE ENABLED - Verbose logging active")

# Initialize router
router = APIRouter()

# Initialize services
game_service = GameService()
ai_service = AIService()
scenario_service = ScenarioService()


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
    try:
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        return game_state

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load game: {str(e)}") from e


# TODO: Separate tasks from routes.py into app/api/tasks.py or something similar
async def process_ai_and_broadcast(game_id: str, message: str) -> None:
    """
    Background task to process AI response and broadcast events.

    Args:
        game_id: Unique game identifier
        message: Player's message/action
    """
    logger.info(f"Starting AI processing for game {game_id}")
    try:
        # Load game state
        game_state = game_service.load_game(game_id)
        if not game_state:
            logger.error(f"Game {game_id} not found")
            await broadcast_service.publish(game_id, "error", {"error": f"Game with ID '{game_id}' not found"})
            return

        # Get AI response using the correct method
        logger.info(f"Requesting AI response for game {game_id}")
        narrative = None

        # Get the AI response (simplified for MVP - no streaming)
        async for chunk in ai_service.generate_response(
            user_message=message,
            game_state=game_state,
            game_service=game_service,
            stream=False,  # MVP: Use non-streaming for simplicity
        ):
            logger.debug(f"Received response: type={chunk.get('type')}")
            if chunk["type"] == "complete":
                narrative = chunk.get("narrative", "")
                break
            elif chunk["type"] == "error":
                logger.error(f"AI error for game {game_id}: {chunk['message']}")
                # Try to get fallback narrative if available
                narrative = chunk.get("narrative", "")
                if not narrative:
                    await broadcast_service.publish(game_id, "error", {"error": chunk["message"]})
                    return

        if not narrative:
            logger.error(f"Failed to get AI response for game {game_id} - narrative is empty")
            # Provide a default response
            narrative = "The tavern is bustling with activity. What would you like to do?"
            logger.info(f"Using fallback narrative for game {game_id}")

            # Still broadcast an error but continue with fallback
            await broadcast_service.publish(
                game_id, "error", {"error": "AI response was empty, using fallback response"}
            )
        logger.info(f"AI response received for game {game_id}")

        # Game state is already updated by tools during AI response generation
        # Reload the updated game state
        updated_game_state = game_service.get_game(game_state.game_id)

        # Messages are already added to conversation history by AIService
        # Just save the final state
        if updated_game_state:
            # Save updated game state
            game_service.save_game(updated_game_state)

            # Send character update
            await message_service.send_character_update(game_id, updated_game_state.character.model_dump())

            # Send final game state update - use model_dump_json then parse to handle datetime
            import json as json_module

            game_state_dict = json_module.loads(updated_game_state.model_dump_json())
            await message_service.send_game_update(game_id, game_state_dict)

        # Send completion event
        await broadcast_service.publish(game_id, "complete", {"status": "success"})
        logger.info(f"AI processing completed successfully for game {game_id}")

    except Exception as e:
        logger.exception(f"Error in AI processing for game {game_id}: {e}")
        # Broadcast error event
        await broadcast_service.publish(game_id, "error", {"error": str(e), "type": type(e).__name__})


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
    try:
        # Verify game exists
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        async def event_generator() -> AsyncGenerator[dict[str, str], None]:
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
