"""CharacterInstance model representing dynamic runtime state for a character."""

from __future__ import annotations

from app.models.character import CharacterSheet
from app.models.instances.base_instance import BaseInstance
from app.models.instances.entity_state import EntityState


class CharacterInstance(BaseInstance):
    """Dynamic character state."""

    template_id: str

    # Embedded snapshot of the character template (trimmed in later phase)
    sheet: CharacterSheet
    # Dynamic runtime state
    state: EntityState

    @property
    def display_name(self) -> str:
        """Human-readable name used across UI/combat."""
        return self.sheet.name
