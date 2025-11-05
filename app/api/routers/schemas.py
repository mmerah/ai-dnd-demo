"""Schema export endpoint for frontend type generation."""

from fastapi import APIRouter

from app.models.ai_response import (
    AIStreamChunk,
    AICompleteResponse,
    AIErrorResponse,
)
from app.models.character import Character
from app.models.combat import Combat, Combatant, Initiative
from app.models.damage_types import DamageType
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import Location
from app.models.memory import MemoryEntry
from app.models.npc import NPC
from app.models.party import Party
from app.models.quest import Quest
from app.models.spell import Spell
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
        "Character": Character.model_json_schema(),
        "Combat": Combat.model_json_schema(),
        "Combatant": Combatant.model_json_schema(),
        "Initiative": Initiative.model_json_schema(),
        "Location": Location.model_json_schema(),
        "Party": Party.model_json_schema(),
        "Quest": Quest.model_json_schema(),
        "NPC": NPC.model_json_schema(),
        "MemoryEntry": MemoryEntry.model_json_schema(),
        # Instance models (display snapshots)
        "CharacterInstance": CharacterInstance.model_json_schema(),
        "MonsterInstance": MonsterInstance.model_json_schema(),
        "ScenarioInstance": ScenarioInstance.model_json_schema(),
        # AI response models
        "AIStreamChunk": AIStreamChunk.model_json_schema(),
        "AICompleteResponse": AICompleteResponse.model_json_schema(),
        "AIErrorResponse": AIErrorResponse.model_json_schema(),
        # Tool models
        "ToolSuggestion": ToolSuggestion.model_json_schema(),
        # Data models
        "Spell": Spell.model_json_schema(),
        "DamageType": DamageType.model_json_schema(),
    }
