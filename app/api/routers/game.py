"""Game endpoints: new/resume/action/equip/SSE and retrieval."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import get_game_state_from_path
from app.api.player_actions import execute_player_action
from app.api.tasks import process_ai_and_broadcast
from app.container import container
from app.events.commands.inventory_commands import EquipItemCommand
from app.models.attributes import EntityType
from app.models.game_state import GameState
from app.models.player_journal import PlayerJournalEntry
from app.models.requests import (
    AcceptCombatSuggestionRequest,
    AcceptCombatSuggestionResponse,
    CreateJournalEntryRequest,
    CreateJournalEntryResponse,
    DeleteJournalEntryResponse,
    EquipItemRequest,
    EquipItemResponse,
    NewGameRequest,
    NewGameResponse,
    PlayerActionRequest,
    RemoveGameResponse,
    ResumeGameResponse,
    UpdateJournalEntryRequest,
    UpdateJournalEntryResponse,
)
from app.models.tool_results import EquipItemResult

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
            content_packs=request.content_packs,
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
async def get_game_state(game_state: GameState = Depends(get_game_state_from_path)) -> GameState:
    """
    Get the complete game state for a session.

    Args:
        game_state: The game state loaded via dependency injection

    Returns:
        Complete game state including character, NPCs, location, etc.
    """
    return game_state


@router.post("/game/{game_id}/resume", response_model=ResumeGameResponse)
async def resume_game(game_state: GameState = Depends(get_game_state_from_path)) -> ResumeGameResponse:
    """
    Resume a saved game session.

    Args:
        game_state: The game state loaded via dependency injection

    Returns:
        Confirmation with game_id
    """
    return ResumeGameResponse(game_id=game_state.game_id, status="resumed")


@router.delete("/game/{game_id}", response_model=RemoveGameResponse)
async def remove_game(game_id: str) -> RemoveGameResponse:
    """
    Remove a game from memory.

    Args:
        game_id: Unique game identifier

    Returns:
        Confirmation with game_id and status

    Raises:
        HTTPException: If removal fails
    """
    game_service = container.game_service

    try:
        game_service.remove_game(game_id)
        return RemoveGameResponse(game_id=game_id, status="removed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove game: {e!s}") from e


@router.post("/game/{game_id}/action")
async def process_player_action(
    request: PlayerActionRequest,
    background_tasks: BackgroundTasks,
    game_state: GameState = Depends(get_game_state_from_path),
) -> dict[str, str]:
    """
    Process a player action and trigger AI response processing.

    Args:
        request: Player's message/action
        background_tasks: FastAPI background tasks for async processing
        game_state: The game state loaded via dependency injection

    Returns:
        Status acknowledgment
    """
    logger.info(f"Processing action for game {game_state.game_id}: {request.message[:50]}...")
    background_tasks.add_task(process_ai_and_broadcast, game_state.game_id, request.message)
    return {"status": "action received"}


@router.post("/game/{game_id}/combat/suggestion/accept", response_model=AcceptCombatSuggestionResponse)
async def accept_combat_suggestion(
    request: AcceptCombatSuggestionRequest,
    background_tasks: BackgroundTasks,
    game_state: GameState = Depends(get_game_state_from_path),
) -> AcceptCombatSuggestionResponse:
    """
    Accept a combat suggestion from an allied NPC and process it.

    This endpoint receives the suggestion data that was previously broadcast via SSE,
    sends it to the combat agent for narration, and advances combat to the next turn.

    Args:
        request: The suggestion data (npc_id, npc_name, action_text, suggestion_id)
        background_tasks: FastAPI background tasks for async processing
        game_state: The game state loaded via dependency injection

    Returns:
        Confirmation that the suggestion was accepted

    Raises:
        HTTPException: If the game is not in combat or other validation fails
    """
    # Validate that combat is active
    if not game_state.combat.is_active:
        raise HTTPException(status_code=400, detail="Combat is not active")

    # Base description that downstream orchestration will wrap with ally instructions
    message = f"{request.npc_name} performs: {request.action_text}"

    logger.info(
        f"Accepting combat suggestion {request.suggestion_id} for game {game_state.game_id}: "
        f"{request.npc_name} - {request.action_text[:50]}..."
    )

    # Process via AI (same pattern as player actions)
    background_tasks.add_task(process_ai_and_broadcast, game_state.game_id, message)

    return AcceptCombatSuggestionResponse(status="suggestion accepted")


@router.post("/game/{game_id}/equip", response_model=EquipItemResponse)
async def equip_item(game_id: str, request: EquipItemRequest) -> EquipItemResponse:
    """Equip or unequip an item for an entity (player or NPC) and recompute derived stats.

    Args:
        game_id: Unique game identifier
        request: EquipItemRequest with item, entity, and slot information

    Returns:
        EquipItemResponse with updated armor class

    Notes:
        - Supports only one-unit operations per call; bulk equip/unequip is not supported
        - Constraints enforced: at most one shield equipped and at most one body armor equipped at a time
    """
    game_service = container.game_service
    action_service = container.action_service

    try:
        # Get the game state
        game_state = game_service.get_game(game_id)

        # Convert entity_type string to enum
        entity_type = EntityType(request.entity_type)

        # Create command
        command = EquipItemCommand(
            game_id=game_id,
            entity_id=request.entity_id,
            entity_type=entity_type,
            item_index=request.item_index,
            slot=request.slot,
            unequip=request.unequip,
        )

        # Execute with event tracking (treating this as a player "tool")
        result: BaseModel = await execute_player_action(
            command=command,
            tool_name="equip_item",
            game_state=game_state,
            action_service=action_service,
        )

        # Extract the result data
        if not isinstance(result, EquipItemResult):
            raise ValueError("Failed to equip item - invalid result type")

        # Get the entity to return its AC
        entity = game_state.get_entity_by_id(entity_type, request.entity_id)
        if not entity:
            raise ValueError("Entity not found after equip operation")

        return EquipItemResponse(
            game_id=game_id,
            item_index=result.item_index,
            equipped=result.equipped,
            slot=result.slot,
            new_armor_class=entity.state.armor_class,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid game data: {e!s}") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to equip item: {e!s}") from e


@router.post("/game/{game_id}/journal", response_model=CreateJournalEntryResponse)
async def create_journal_entry(
    request: CreateJournalEntryRequest, game_state: GameState = Depends(get_game_state_from_path)
) -> CreateJournalEntryResponse:
    """Create a new player journal entry with auto-linked location and NPC tags.

    Args:
        request: CreateJournalEntryRequest with content and optional tags
        game_state: The game state loaded via dependency injection

    Returns:
        CreateJournalEntryResponse with the created entry

    Raises:
        HTTPException: If creation fails
    """
    game_service = container.game_service
    journal_service = container.player_journal_service

    entry = journal_service.create_entry(game_state, request.content, request.tags)
    game_service.save_game(game_state)
    return CreateJournalEntryResponse(entry=entry)


@router.get("/game/{game_id}/journal", response_model=list[PlayerJournalEntry])
async def list_journal_entries(game_state: GameState = Depends(get_game_state_from_path)) -> list[PlayerJournalEntry]:
    """List all player journal entries for a game.

    Args:
        game_state: The game state loaded via dependency injection

    Returns:
        List of all journal entries
    """
    journal_service = container.player_journal_service
    return journal_service.list_entries(game_state)


@router.get("/game/{game_id}/journal/{entry_id}", response_model=PlayerJournalEntry)
async def get_journal_entry(
    entry_id: str, game_state: GameState = Depends(get_game_state_from_path)
) -> PlayerJournalEntry:
    """Get a specific journal entry by ID.

    Args:
        entry_id: Unique journal entry identifier
        game_state: The game state loaded via dependency injection

    Returns:
        The requested journal entry

    Raises:
        HTTPException: If entry not found
    """
    journal_service = container.player_journal_service
    entry = journal_service.get_entry(game_state, entry_id)

    if entry is None:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    return entry


@router.put("/game/{game_id}/journal/{entry_id}", response_model=UpdateJournalEntryResponse)
async def update_journal_entry(
    entry_id: str, request: UpdateJournalEntryRequest, game_state: GameState = Depends(get_game_state_from_path)
) -> UpdateJournalEntryResponse:
    """Update an existing journal entry's content and tags.

    Args:
        entry_id: Unique journal entry identifier
        request: UpdateJournalEntryRequest with new content and tags
        game_state: The game state loaded via dependency injection

    Returns:
        UpdateJournalEntryResponse with the updated entry

    Raises:
        HTTPException: If entry not found
    """
    game_service = container.game_service
    journal_service = container.player_journal_service

    # Get existing entry to preserve status
    existing_entry = journal_service.get_entry(game_state, entry_id)
    if existing_entry is None:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    updated_entry = journal_service.update_entry(
        game_state, entry_id, request.content, request.tags, pinned=existing_entry.pinned
    )

    if updated_entry is None:
        raise HTTPException(status_code=500, detail=f"Failed to update journal entry {entry_id}")

    game_service.save_game(game_state)
    return UpdateJournalEntryResponse(entry=updated_entry)


@router.delete("/game/{game_id}/journal/{entry_id}", response_model=DeleteJournalEntryResponse)
async def delete_journal_entry(
    entry_id: str, game_state: GameState = Depends(get_game_state_from_path)
) -> DeleteJournalEntryResponse:
    """Delete a journal entry by ID.

    Args:
        entry_id: Unique journal entry identifier
        game_state: The game state loaded via dependency injection

    Returns:
        DeleteJournalEntryResponse with success status

    Raises:
        HTTPException: If entry not found
    """
    game_service = container.game_service
    journal_service = container.player_journal_service

    success = journal_service.delete_entry(game_state, entry_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    game_service.save_game(game_state)
    return DeleteJournalEntryResponse(success=True, entry_id=entry_id)


@router.patch("/game/{game_id}/journal/{entry_id}/pin", response_model=UpdateJournalEntryResponse)
async def toggle_pin_journal_entry(
    entry_id: str, game_state: GameState = Depends(get_game_state_from_path)
) -> UpdateJournalEntryResponse:
    """Toggle the pinned status of a journal entry.

    Args:
        entry_id: Unique journal entry identifier
        game_state: The game state loaded via dependency injection

    Returns:
        UpdateJournalEntryResponse with the updated entry

    Raises:
        HTTPException: If entry not found
    """
    game_service = container.game_service
    journal_service = container.player_journal_service

    # Get the entry
    entry = journal_service.get_entry(game_state, entry_id)

    if entry is None:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    # Toggle pinned status (handle old saves where pinned might be None)
    current_pinned = entry.pinned if entry.pinned is not None else False
    updated_entry = journal_service.update_entry(
        game_state, entry_id, content=entry.content, tags=entry.tags, pinned=not current_pinned
    )

    if updated_entry is None:
        raise HTTPException(status_code=500, detail=f"Failed to update journal entry {entry_id}")

    game_service.save_game(game_state)
    return UpdateJournalEntryResponse(entry=updated_entry)


@router.get("/game/{game_id}/sse")
async def game_sse_endpoint(game_state: GameState = Depends(get_game_state_from_path)) -> EventSourceResponse:
    """
    SSE endpoint for real-time game updates.

    This endpoint maintains a persistent connection for pushing
    game state updates, dice roll results, and other events.

    Args:
        game_state: The game state loaded via dependency injection

    Returns:
        SSE stream for real-time updates
    """
    message_service = container.message_service
    scenario_service = container.scenario_service
    scenario = game_state.scenario_instance.sheet
    available_scenarios = scenario_service.list_scenarios()
    return EventSourceResponse(
        message_service.generate_sse_events(
            game_state.game_id,
            game_state,
            scenario,
            available_scenarios,
        )
    )
