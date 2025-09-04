"""CharacterInstance model representing dynamic runtime state for a character."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.character import CharacterSheet
from app.models.instances.entity_state import EntityState


class CharacterInstance(BaseModel):
    """Dynamic character state."""

    # Identity
    instance_id: str
    template_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Embedded snapshot of the character template (trimmed in later phase)
    sheet: CharacterSheet
    # Dynamic runtime state
    state: EntityState

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now()
