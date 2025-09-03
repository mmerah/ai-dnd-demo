"""NPC wrapper model for scenario-defined NPCs embedding a CharacterSheet."""

from pydantic import BaseModel, Field

from app.models.character import CharacterSheet


class NPCSheet(BaseModel):
    """NPC wrapper embedding a full CharacterSheet plus scenario metadata."""

    # Scenario identity (stable within scenario)
    id: str
    display_name: str
    role: str
    description: str

    # Scenario presentation
    dialogue_hints: list[str] = Field(default_factory=list)
    attitude: str | None = None  # friendly, hostile, neutral, etc.
    notes: list[str] = Field(default_factory=list)

    # Embedded character profile
    character: CharacterSheet

    # Presence flags (optional runtime)
    present: bool = True

    def is_alive(self) -> bool:
        """NPC considered alive if embedded character has HP > 0."""
        return self.character.hit_points.current > 0
