"""NPC wrapper model for scenario-defined NPCs embedding a CharacterSheet."""

from enum import Enum

from pydantic import BaseModel, Field

from app.models.character import CharacterSheet


class NPCImportance(str, Enum):
    """Classification for NPC routing importance."""

    MAJOR = "major"
    MINOR = "minor"


class NPCSheet(BaseModel):
    """NPC wrapper embedding a full CharacterSheet plus scenario metadata (template-only)."""

    # Scenario identity (stable within scenario)
    id: str
    display_name: str
    role: str
    description: str
    initial_location_id: str
    importance: NPCImportance = NPCImportance.MINOR

    # Scenario presentation seeds (initial values)
    initial_dialogue_hints: list[str] = Field(default_factory=list)
    initial_attitude: str | None = None
    initial_notes: list[str] = Field(default_factory=list)

    # Embedded character template
    character: CharacterSheet
