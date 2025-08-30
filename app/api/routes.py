"""
API routes for D&D 5e AI Dungeon Master.
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.tasks import process_ai_and_broadcast
from app.container import container
from app.models.api_responses import (
    ActionAcknowledgement,
    GameStatusResponse,
    ItemDetailResponse,
    SavedGameSummary,
    ScenarioDetailResponse,
    ScenarioSummaryResponse,
    SpellDetailResponse,
)
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.requests import NewGameRequest, NewGameResponse, PlayerActionRequest
from app.models.sse_events import (
    ActUpdateData,
    ConnectionInfo,
    InitialNarrativeData,
    LocationUpdateData,
    QuestUpdateData,
    ScenarioInfoData,
    ScenarioSummary,
    SSEEvent,
    SSEEventType,
)
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
    character_service = container.get_character_service()

    try:
        # Get the selected character
        character = character_service.get_character(request.character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"Character with ID '{request.character_id}' not found")

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


@router.get("/games", response_model=list[SavedGameSummary])
async def list_saved_games() -> list[SavedGameSummary]:
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
        return [SavedGameSummary(**game) for game in saved_games]
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


@router.post("/game/{game_id}/resume", response_model=GameStatusResponse)
async def resume_game(game_id: str) -> GameStatusResponse:
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
        return GameStatusResponse(game_id=game_id, status="resumed")

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume game: {str(e)}") from e


@router.post("/game/{game_id}/action", response_model=ActionAcknowledgement)
async def process_player_action(
    game_id: str, request: PlayerActionRequest, background_tasks: BackgroundTasks
) -> ActionAcknowledgement:
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
        return ActionAcknowledgement(status="action received")

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
                initial_event = SSEEvent(
                    event=SSEEventType.INITIAL_NARRATIVE,
                    data=InitialNarrativeData(
                        scenario_title=game_state.scenario_title or "Custom Adventure",
                        narrative=game_state.conversation_history[0].content,
                    ),
                )
                yield initial_event.to_sse_format()

            # Send scenario info if available
            if game_state.scenario_id:
                scenarios = scenario_service.list_scenarios()
                scenario_event = SSEEvent(
                    event=SSEEventType.SCENARIO_INFO,
                    data=ScenarioInfoData(
                        current_scenario=ScenarioSummary(
                            id=game_state.scenario_id, title=game_state.scenario_title or ""
                        ),
                        available_scenarios=[
                            ScenarioSummary(id=s.id, title=s.title, description=s.description) for s in scenarios
                        ],
                    ),
                )
                yield scenario_event.to_sse_format()

                # Send location info if available
                scenario = scenario_service.get_scenario(game_state.scenario_id)
                if scenario and game_state.current_location_id:
                    location = scenario.get_location(game_state.current_location_id)
                    if location:
                        location_state = game_state.get_location_state(game_state.current_location_id)
                        connections = [
                            ConnectionInfo(
                                to_location_id=conn.to_location_id,
                                description=conn.description,
                                direction=conn.direction,
                                is_accessible=conn.can_traverse(),
                                is_visible=conn.is_visible,
                            )
                            for conn in location.connections
                        ]

                        location_event = SSEEvent(
                            event=SSEEventType.LOCATION_UPDATE,
                            data=LocationUpdateData(
                                location_id=location.id,
                                location_name=location.name,
                                description=location.get_description(location_state.get_description_variant()),
                                connections=connections,
                                danger_level=location_state.danger_level.value,
                                npcs_present=location_state.npcs_present,
                            ),
                        )
                        yield location_event.to_sse_format()

                # Send quest info
                active_quests_data = [quest.model_dump() for quest in game_state.active_quests]
                quest_event = SSEEvent(
                    event=SSEEventType.QUEST_UPDATE,
                    data=QuestUpdateData(
                        active_quests=active_quests_data, completed_quest_ids=game_state.completed_quest_ids
                    ),
                )
                yield quest_event.to_sse_format()

                # Send act info
                if scenario:
                    current_act = scenario.progression.get_current_act()
                    if current_act:
                        act_event = SSEEvent(
                            event=SSEEventType.ACT_UPDATE,
                            data=ActUpdateData(
                                act_id=current_act.id,
                                act_name=current_act.name,
                                act_index=scenario.progression.current_act_index,
                            ),
                        )
                        yield act_event.to_sse_format()

            async for event_data in broadcast_service.subscribe(game_id):
                # event_data is already in SSE format from broadcast_service
                if event_data["event"] != "narrative":
                    logger.debug(f"Sending SSE event '{event_data['event']}' to game {game_id}")
                yield event_data

        return EventSourceResponse(event_generator())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to establish SSE connection: {str(e)}") from e


@router.get("/scenarios", response_model=list[ScenarioSummaryResponse])
async def list_available_scenarios() -> list[ScenarioSummaryResponse]:
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
        return scenarios  # Already returns list[ScenarioSummaryResponse]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenarios: {str(e)}") from e


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(scenario_id: str) -> ScenarioDetailResponse:
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

        return ScenarioDetailResponse(
            id=scenario.id,
            title=scenario.title,
            description=scenario.description,
            starting_location=scenario.starting_location,
        )

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
    character_service = container.get_character_service()

    try:
        # Get all characters from the service
        characters = character_service.get_all_characters()
        return characters

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load characters: {str(e)}") from e


@router.get("/items/{item_name}", response_model=ItemDetailResponse)
async def get_item_details(item_name: str) -> ItemDetailResponse:
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

        return ItemDetailResponse(
            name=item.name,
            type=item.type.value,
            rarity=item.rarity.value,
            weight=item.weight,
            value=item.value,
            description=item.description,
            damage=item.damage,
            damage_type=item.damage_type,
            properties=item.properties,
            armor_class=item.armor_class,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get item details: {str(e)}") from e


@router.get("/spells/{spell_name}", response_model=SpellDetailResponse)
async def get_spell_details(spell_name: str) -> SpellDetailResponse:
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

        return SpellDetailResponse(
            name=spell.name,
            level=spell.level,
            school=spell.school.value,
            casting_time=spell.casting_time,
            range=spell.range,
            components=spell.components,
            duration=spell.duration,
            description=spell.description,
            higher_levels=spell.higher_levels,
            classes=spell.classes,
            ritual=spell.ritual,
            concentration=spell.concentration,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get spell details: {str(e)}") from e
