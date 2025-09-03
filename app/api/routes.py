"""
API routes for D&D 5e AI Dungeon Master.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.tasks import process_ai_and_broadcast
from app.container import container
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition

# Import core models directly instead of duplicate API response models
from app.models.character import CharacterSheet
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.condition import Condition
from app.models.damage_type import DamageType
from app.models.feat import FeatDefinition as FeatDef
from app.models.feature import FeatureDefinition as FeatureDef
from app.models.game_state import GameState
from app.models.item import ItemDefinition
from app.models.language import Language
from app.models.magic_school import MagicSchool
from app.models.monster import Monster
from app.models.race import RaceDefinition
from app.models.race import SubraceDefinition as RaceSubraceDefinition
from app.models.requests import NewGameRequest, NewGameResponse, PlayerActionRequest
from app.models.scenario import Scenario
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition as TraitDef
from app.models.weapon_property import WeaponProperty

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
    game_service = container.game_service
    character_service = container.character_service

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
    game_service = container.game_service

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
    game_service = container.game_service

    try:
        # load_game raises FileNotFoundError or ValueError on failure
        game_state = game_service.load_game(game_id)
        return game_state

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid game data: {e!s}") from e
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
    game_service = container.game_service

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
    game_service = container.game_service

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
    game_service = container.game_service

    try:
        # Verify game exists
        game_state = game_service.load_game(game_id)
        if not game_state:
            raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found")

        # Get services
        message_service = container.message_service
        scenario_service = container.scenario_service

        # Get scenario info if available
        scenario = None
        available_scenarios = None
        if game_state.scenario_id:
            scenario = scenario_service.get_scenario(game_state.scenario_id)
            available_scenarios = scenario_service.list_scenarios()

        # Use MessageService to generate SSE events
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


@router.get("/scenarios")
async def list_available_scenarios() -> list[Scenario]:
    """
    List all available scenarios.

    Returns:
        List of scenario summaries

    Raises:
        HTTPException: If scenarios cannot be loaded
    """
    scenario_service = container.scenario_service

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
    scenario_service = container.scenario_service

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
    character_service = container.character_service

    try:
        # Get all characters from the service
        characters = character_service.get_all_characters()
        return characters

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load characters: {e!s}") from e


# === CATALOG ENDPOINTS ===
# All catalog data follows a consistent pattern:
#   /catalogs/{type} - list all (with ?keys_only=true for just keys)
#   /catalogs/{type}/{index} - get specific item by index/key


# Items
@router.get("/catalogs/items")
async def list_items(keys_only: bool = False) -> list[ItemDefinition] | list[str]:
    """List all items (full objects by default, or keys with ?keys_only=true)."""
    repo = container.item_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[ItemDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/items/{index}")
async def get_item(index: str) -> ItemDefinition:
    repo = container.item_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{index}' not found")
    return item


# Spells
@router.get("/catalogs/spells")
async def list_spells(keys_only: bool = False) -> list[SpellDefinition] | list[str]:
    """List all spells (full objects by default, or keys with ?keys_only=true)."""
    repo = container.spell_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[SpellDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/spells/{index}")
async def get_spell(index: str) -> SpellDefinition:
    repo = container.spell_repository
    spell = repo.get(index)
    if not spell:
        raise HTTPException(status_code=404, detail=f"Spell '{index}' not found")
    return spell


# Monsters
@router.get("/catalogs/monsters")
async def list_monsters(keys_only: bool = False) -> list[Monster] | list[str]:
    """List all monsters (full objects by default, or keys with ?keys_only=true)."""
    repo = container.monster_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[Monster] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/monsters/{index}")
async def get_monster(index: str) -> Monster:
    repo = container.monster_repository
    monster = repo.get(index)
    if not monster:
        raise HTTPException(status_code=404, detail=f"Monster '{index}' not found")
    return monster


# Magic Schools
@router.get("/catalogs/magic_schools")
async def list_magic_schools(keys_only: bool = False) -> list[MagicSchool] | list[str]:
    repo = container.magic_school_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[MagicSchool] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/magic_schools/{index}")
async def get_magic_school(index: str) -> MagicSchool:
    repo = container.magic_school_repository
    ms = repo.get(index)
    if not ms:
        raise HTTPException(status_code=404, detail=f"Magic school '{index}' not found")
    return ms


# Alignment
@router.get("/catalogs/alignments")
async def list_alignments(keys_only: bool = False) -> list[Alignment] | list[str]:
    repo = container.alignment_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Alignment] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/alignments/{index}")
async def get_alignment(index: str) -> Alignment:
    repo = container.alignment_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Alignment '{index}' not found")
    return item


# Classes
@router.get("/catalogs/classes")
async def list_classes(keys_only: bool = False) -> list[ClassDefinition] | list[str]:
    repo = container.class_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[ClassDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/classes/{index}")
async def get_class(index: str) -> ClassDefinition:
    repo = container.class_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Class '{index}' not found")
    return item


# Subclasses
@router.get("/catalogs/subclasses")
async def list_subclasses(keys_only: bool = False) -> list[SubclassDefinition] | list[str]:
    repo = container.subclass_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[SubclassDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/subclasses/{index}")
async def get_subclass(index: str) -> SubclassDefinition:
    repo = container.subclass_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Subclass '{index}' not found")
    return item


# Languages
@router.get("/catalogs/languages")
async def list_languages(keys_only: bool = False) -> list[Language] | list[str]:
    repo = container.language_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Language] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/languages/{index}")
async def get_language(index: str) -> Language:
    repo = container.language_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Language '{index}' not found")
    return item


# Conditions
@router.get("/catalogs/conditions")
async def list_conditions(keys_only: bool = False) -> list[Condition] | list[str]:
    repo = container.condition_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Condition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/conditions/{index}")
async def get_condition(index: str) -> Condition:
    repo = container.condition_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Condition '{index}' not found")
    return item


# Races
@router.get("/catalogs/races")
async def list_races(keys_only: bool = False) -> list[RaceDefinition] | list[str]:
    repo = container.race_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[RaceDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/races/{index}")
async def get_race(index: str) -> RaceDefinition:
    repo = container.race_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Race '{index}' not found")
    return item


# Subraces
@router.get("/catalogs/race_subraces")
async def list_race_subraces(keys_only: bool = False) -> list[RaceSubraceDefinition] | list[str]:
    repo = container.race_subrace_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[RaceSubraceDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/race_subraces/{index}")
async def get_race_subrace(index: str) -> RaceSubraceDefinition:
    repo = container.race_subrace_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Subrace '{index}' not found")
    return item


# Backgrounds
@router.get("/catalogs/backgrounds")
async def list_backgrounds(keys_only: bool = False) -> list[BackgroundDefinition] | list[str]:
    repo = container.background_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[BackgroundDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/backgrounds/{index}")
async def get_background(index: str) -> BackgroundDefinition:
    repo = container.background_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Background '{index}' not found")
    return item


# Traits
@router.get("/catalogs/traits")
async def list_traits(keys_only: bool = False) -> list[TraitDef] | list[str]:
    repo = container.trait_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[TraitDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/traits/{index}")
async def get_trait(index: str) -> TraitDef:
    repo = container.trait_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Trait '{index}' not found")
    return item


# Features
@router.get("/catalogs/features")
async def list_features(keys_only: bool = False) -> list[FeatureDef] | list[str]:
    repo = container.feature_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[FeatureDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/features/{index}")
async def get_feature(index: str) -> FeatureDef:
    repo = container.feature_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Feature '{index}' not found")
    return item


# Feats
@router.get("/catalogs/feats")
async def list_feats(keys_only: bool = False) -> list[FeatDef] | list[str]:
    repo = container.feat_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[FeatDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/feats/{index}")
async def get_feat(index: str) -> FeatDef:
    repo = container.feat_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Feat '{index}' not found")
    return item


# Skills
@router.get("/catalogs/skills")
async def list_skills(keys_only: bool = False) -> list[Skill] | list[str]:
    repo = container.skill_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[Skill] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/skills/{index}")
async def get_skill(index: str) -> Skill:
    repo = container.skill_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Skill '{index}' not found")
    return item


# Weapon Properties
@router.get("/catalogs/weapon_properties")
async def list_weapon_properties(keys_only: bool = False) -> list[WeaponProperty] | list[str]:
    repo = container.weapon_property_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[WeaponProperty] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/weapon_properties/{index}")
async def get_weapon_property(index: str) -> WeaponProperty:
    repo = container.weapon_property_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Weapon property '{index}' not found")
    return item


# Damage Types
@router.get("/catalogs/damage_types")
async def list_damage_types(keys_only: bool = False) -> list[DamageType] | list[str]:
    repo = container.damage_type_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[DamageType] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/damage_types/{index}")
async def get_damage_type(index: str) -> DamageType:
    repo = container.damage_type_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Damage type '{index}' not found")
    return item
