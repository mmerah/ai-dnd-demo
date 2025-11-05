"""Schema export endpoint for frontend type generation."""

from fastapi import APIRouter

from app.models.ai_response import (
    NarrativeChunkResponse,
    CompleteResponse,
    ErrorResponse,
)
from app.models.character import CharacterSheet
from app.models.combat import CombatState, CombatParticipant
from app.models.damage_type import DamageType
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.models.memory import MemoryEntry
from app.models.npc import NPCSheet
from app.models.party import PartyState
from app.models.spell import SpellDefinition
from app.models.tool_suggestion import ToolSuggestion

router = APIRouter()


@router.get("/schemas")
async def get_schemas() -> dict[str, dict]:
    """Export JSON schemas for all Pydantic models used in API responses.

    This endpoint is used by the frontend type generation script to create
    TypeScript interfaces that match the backend models exactly.

    Returns:
        dict[str, dict]: Map of model name to JSON schema
    """
    return {
        # Core game models
        "GameState": GameState.model_json_schema(),
        "CharacterSheet": CharacterSheet.model_json_schema(),
        "CombatState": CombatState.model_json_schema(),
        "CombatParticipant": CombatParticipant.model_json_schema(),
        "LocationState": LocationState.model_json_schema(),
        "PartyState": PartyState.model_json_schema(),
        "NPCSheet": NPCSheet.model_json_schema(),
        "MemoryEntry": MemoryEntry.model_json_schema(),
        # Instance models (display snapshots)
        "CharacterInstance": CharacterInstance.model_json_schema(),
        "MonsterInstance": MonsterInstance.model_json_schema(),
        "ScenarioInstance": ScenarioInstance.model_json_schema(),
        # AI response models
        "NarrativeChunkResponse": NarrativeChunkResponse.model_json_schema(),
        "CompleteResponse": CompleteResponse.model_json_schema(),
        "ErrorResponse": ErrorResponse.model_json_schema(),
        # Tool models
        "ToolSuggestion": ToolSuggestion.model_json_schema(),
        # Data models
        "SpellDefinition": SpellDefinition.model_json_schema(),
        "DamageType": DamageType.model_json_schema(),
    }
