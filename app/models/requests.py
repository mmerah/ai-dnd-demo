from typing import Literal

from pydantic import BaseModel, Field

from app.models.player_journal import PlayerJournalEntry


class NewGameRequest(BaseModel):
    """Request model for creating a new game."""

    character_id: str = Field(..., description="ID of the character to play")
    scenario_id: str = Field(..., description="ID of the scenario to play")
    content_packs: list[str] | None = Field(None, description="Additional content packs to use with scenario")


class NewGameResponse(BaseModel):
    """Response model for new game creation."""

    game_id: str = Field(..., description="Unique identifier for the game")


class ResumeGameResponse(BaseModel):
    """Response model for resuming a saved game."""

    game_id: str = Field(..., description="Unique identifier for the resumed game")
    status: str = Field(..., description="Resume status, typically 'resumed'")


class RemoveGameResponse(BaseModel):
    """Response model for removing a game."""

    game_id: str = Field(..., description="ID of the removed game")
    status: str = Field(..., description="Removal status, typically 'removed'")


class PlayerActionRequest(BaseModel):
    """Request model for player actions."""

    message: str = Field(..., description="Player's message/action")


class EquipItemRequest(BaseModel):
    """Request model to equip or unequip a specific inventory item for an entity (player or NPC)."""

    item_index: str = Field(..., description="Index of the item in inventory")
    entity_id: str = Field(..., description="Instance ID of entity")
    entity_type: Literal["player", "npc"] = Field(..., description="Type of entity ('player' or 'npc')")
    slot: (
        Literal[
            "head",
            "neck",
            "chest",
            "hands",
            "feet",
            "waist",
            "main_hand",
            "off_hand",
            "ring_1",
            "ring_2",
            "back",
            "ammunition",
        ]
        | None
    ) = Field(None, description="Target equipment slot. Auto-selects if not specified.")
    unequip: bool = Field(False, description="True to unequip from slots")


class EquipItemResponse(BaseModel):
    """Response model for equip/unequip operations."""

    game_id: str
    item_index: str
    equipped: bool
    slot: str | None
    new_armor_class: int


class ResolveNamesRequest(BaseModel):
    """Request model for resolving catalog names from indexes."""

    game_id: str = Field(..., description="Game ID for content pack scoping")
    items: list[str] | None = Field(None, description="Item indexes to resolve")
    spells: list[str] | None = Field(None, description="Spell indexes to resolve")
    monsters: list[str] | None = Field(None, description="Monster indexes to resolve")
    classes: list[str] | None = Field(None, description="Class indexes to resolve")
    races: list[str] | None = Field(None, description="Race indexes to resolve")
    alignments: list[str] | None = Field(None, description="Alignment indexes to resolve")
    backgrounds: list[str] | None = Field(None, description="Background indexes to resolve")
    feats: list[str] | None = Field(None, description="Feat indexes to resolve")
    features: list[str] | None = Field(None, description="Feature indexes to resolve")
    traits: list[str] | None = Field(None, description="Trait indexes to resolve")
    skills: list[str] | None = Field(None, description="Skill indexes to resolve")
    conditions: list[str] | None = Field(None, description="Condition indexes to resolve")
    languages: list[str] | None = Field(None, description="Language indexes to resolve")
    damage_types: list[str] | None = Field(None, description="Damage Types indexes to resolve")
    magic_schools: list[str] | None = Field(None, description="Magic Schools indexes to resolve")
    subclasses: list[str] | None = Field(None, description="Subclasses indexes to resolve")
    subraces: list[str] | None = Field(None, description="Subraces indexes to resolve")
    weapon_properties: list[str] | None = Field(None, description="Weapon Properties indexes to resolve")


class ResolveNamesResponse(BaseModel):
    """Response model for resolved catalog names."""

    items: dict[str, str] = Field(default_factory=dict, description="Item index to name mapping")
    spells: dict[str, str] = Field(default_factory=dict, description="Spell index to name mapping")
    monsters: dict[str, str] = Field(default_factory=dict, description="Monster index to name mapping")
    classes: dict[str, str] = Field(default_factory=dict, description="Class index to name mapping")
    races: dict[str, str] = Field(default_factory=dict, description="Race index to name mapping")
    alignments: dict[str, str] = Field(default_factory=dict, description="Alignment Index to name mapping")
    backgrounds: dict[str, str] = Field(default_factory=dict, description="Background index to name mapping")
    feats: dict[str, str] = Field(default_factory=dict, description="Feat index to name mapping")
    features: dict[str, str] = Field(default_factory=dict, description="Feature index to name mapping")
    traits: dict[str, str] = Field(default_factory=dict, description="Trait index to name mapping")
    skills: dict[str, str] = Field(default_factory=dict, description="Skill index to name mapping")
    conditions: dict[str, str] = Field(default_factory=dict, description="Condition index to name mapping")
    languages: dict[str, str] = Field(default_factory=dict, description="Language index to name mapping")
    damage_types: dict[str, str] = Field(default_factory=dict, description="Damage Types index to name mapping")
    magic_schools: dict[str, str] = Field(default_factory=dict, description="Magic Schools index to name mapping")
    subclasses: dict[str, str] = Field(default_factory=dict, description="Subclasses index to name mapping")
    subraces: dict[str, str] = Field(default_factory=dict, description="Subraces index to name mapping")
    weapon_properties: dict[str, str] = Field(
        default_factory=dict, description="Weapon Properties index to name mapping"
    )


class AcceptCombatSuggestionRequest(BaseModel):
    """Request model for accepting a combat suggestion from an allied NPC."""

    suggestion_id: str = Field(..., description="Unique identifier for the suggestion being accepted")
    npc_id: str = Field(..., description="Instance ID of the NPC who made the suggestion")
    npc_name: str = Field(..., description="Display name of the NPC")
    action_text: str = Field(..., description="The suggested action text")


class AcceptCombatSuggestionResponse(BaseModel):
    """Response model for accepting a combat suggestion."""

    status: str = Field(..., description="Status message, typically 'suggestion accepted'")


class CreateJournalEntryRequest(BaseModel):
    """Request model for creating a new journal entry."""

    content: str = Field(..., min_length=1, max_length=10000, description="Journal entry text content")
    tags: list[str] = Field(default_factory=list, max_length=50, description="User-defined tags (comma-separated)")


class CreateJournalEntryResponse(BaseModel):
    """Response model for creating a journal entry."""

    entry: PlayerJournalEntry = Field(..., description="The created journal entry")


class UpdateJournalEntryRequest(BaseModel):
    """Request model for updating an existing journal entry."""

    content: str = Field(..., min_length=1, max_length=10000, description="Updated journal entry text content")
    tags: list[str] = Field(default_factory=list, max_length=50, description="Updated user-defined tags")


class UpdateJournalEntryResponse(BaseModel):
    """Response model for updating a journal entry."""

    entry: PlayerJournalEntry = Field(..., description="The updated journal entry")


class DeleteJournalEntryResponse(BaseModel):
    """Response model for deleting a journal entry."""

    success: bool = Field(..., description="True if entry was deleted, False if not found")
    entry_id: str = Field(..., description="ID of the deleted entry")
