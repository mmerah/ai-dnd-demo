"""Schema export endpoint for frontend type generation."""

from typing import Any

from fastapi import APIRouter

from app.api.schemas.content_packs import ContentPackListResponse
from app.models.ai_response import (
    CompleteResponse,
    ErrorResponse,
    NarrativeChunkResponse,
)
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition
from app.models.character import CharacterSheet
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.combat import CombatParticipant, CombatState, CombatSuggestion
from app.models.condition import Condition
from app.models.content_pack import ContentPackSummary
from app.models.damage_type import DamageType
from app.models.feat import FeatDefinition
from app.models.feature import FeatureDefinition
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.item import ItemDefinition
from app.models.language import Language
from app.models.location import LocationState
from app.models.magic_school import MagicSchool
from app.models.memory import MemoryEntry
from app.models.monster import MonsterSheet
from app.models.npc import NPCSheet
from app.models.party import PartyState
from app.models.player_journal import PlayerJournalEntry
from app.models.race import RaceDefinition, SubraceDefinition
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
    RequestAllySuggestionResponse,
    ResolveNamesRequest,
    ResolveNamesResponse,
    ResumeGameResponse,
    UpdateJournalEntryRequest,
    UpdateJournalEntryResponse,
)
from app.models.scenario import ScenarioSheet
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.sse_events import (
    CombatSuggestionData,
    CombatUpdateData,
    CompleteData,
    ConnectedData,
    ErrorData,
    GameUpdateData,
    HeartbeatData,
    InitialNarrativeData,
    NarrativeData,
    NPCDialogueData,
    PolicyWarningData,
    ScenarioInfoData,
    SSEEvent,
    ToolCallData,
    ToolResultData,
)
from app.models.tool_suggestion import ToolSuggestion
from app.models.trait import TraitDefinition
from app.models.weapon_property import WeaponProperty

router = APIRouter()


@router.get("/schemas")
async def get_schemas() -> dict[str, dict[str, Any]]:
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
        "ScenarioSheet": ScenarioSheet.model_json_schema(),
        "CombatState": CombatState.model_json_schema(),
        "CombatParticipant": CombatParticipant.model_json_schema(),
        "CombatSuggestion": CombatSuggestion.model_json_schema(),
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
        # Catalog/Reference data models
        "SpellDefinition": SpellDefinition.model_json_schema(),
        "ItemDefinition": ItemDefinition.model_json_schema(),
        "MonsterSheet": MonsterSheet.model_json_schema(),
        "RaceDefinition": RaceDefinition.model_json_schema(),
        "SubraceDefinition": SubraceDefinition.model_json_schema(),
        "ClassDefinition": ClassDefinition.model_json_schema(),
        "SubclassDefinition": SubclassDefinition.model_json_schema(),
        "BackgroundDefinition": BackgroundDefinition.model_json_schema(),
        "FeatDefinition": FeatDefinition.model_json_schema(),
        "FeatureDefinition": FeatureDefinition.model_json_schema(),
        "TraitDefinition": TraitDefinition.model_json_schema(),
        "Skill": Skill.model_json_schema(),
        "Condition": Condition.model_json_schema(),
        "Language": Language.model_json_schema(),
        "DamageType": DamageType.model_json_schema(),
        "MagicSchool": MagicSchool.model_json_schema(),
        "WeaponProperty": WeaponProperty.model_json_schema(),
        "Alignment": Alignment.model_json_schema(),
        # API Request/Response models
        "NewGameRequest": NewGameRequest.model_json_schema(),
        "NewGameResponse": NewGameResponse.model_json_schema(),
        "ResumeGameResponse": ResumeGameResponse.model_json_schema(),
        "RemoveGameResponse": RemoveGameResponse.model_json_schema(),
        "PlayerActionRequest": PlayerActionRequest.model_json_schema(),
        "EquipItemRequest": EquipItemRequest.model_json_schema(),
        "EquipItemResponse": EquipItemResponse.model_json_schema(),
        "AcceptCombatSuggestionRequest": AcceptCombatSuggestionRequest.model_json_schema(),
        "AcceptCombatSuggestionResponse": AcceptCombatSuggestionResponse.model_json_schema(),
        "RequestAllySuggestionResponse": RequestAllySuggestionResponse.model_json_schema(),
        "CreateJournalEntryRequest": CreateJournalEntryRequest.model_json_schema(),
        "CreateJournalEntryResponse": CreateJournalEntryResponse.model_json_schema(),
        "UpdateJournalEntryRequest": UpdateJournalEntryRequest.model_json_schema(),
        "UpdateJournalEntryResponse": UpdateJournalEntryResponse.model_json_schema(),
        "DeleteJournalEntryResponse": DeleteJournalEntryResponse.model_json_schema(),
        "ResolveNamesRequest": ResolveNamesRequest.model_json_schema(),
        "ResolveNamesResponse": ResolveNamesResponse.model_json_schema(),
        "PlayerJournalEntry": PlayerJournalEntry.model_json_schema(),
        "ContentPackSummary": ContentPackSummary.model_json_schema(),
        "ContentPackListResponse": ContentPackListResponse.model_json_schema(),
        # SSE event models (for frontend SSE type generation)
        "SSEEvent": SSEEvent.model_json_schema(),
        "ConnectedData": ConnectedData.model_json_schema(),
        "HeartbeatData": HeartbeatData.model_json_schema(),
        "NarrativeData": NarrativeData.model_json_schema(),
        "InitialNarrativeData": InitialNarrativeData.model_json_schema(),
        "ToolCallData": ToolCallData.model_json_schema(),
        "ToolResultData": ToolResultData.model_json_schema(),
        "NPCDialogueData": NPCDialogueData.model_json_schema(),
        "PolicyWarningData": PolicyWarningData.model_json_schema(),
        "CombatSuggestionData": CombatSuggestionData.model_json_schema(),
        "ScenarioInfoData": ScenarioInfoData.model_json_schema(),
        "GameUpdateData": GameUpdateData.model_json_schema(),
        "CombatUpdateData": CombatUpdateData.model_json_schema(),
        "ErrorData": ErrorData.model_json_schema(),
        "CompleteData": CompleteData.model_json_schema(),
    }
