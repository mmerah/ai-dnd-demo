"""MonsterInstance model representing a runtime monster in the game.

Separates static template data (MonsterSheet) from mutable runtime state (EntityState),
aligned with CharacterInstance and NPCInstance patterns.
"""

from __future__ import annotations

from app.models.instances.base_instance import BaseInstance
from app.models.instances.entity_state import EntityState
from app.models.monster import MonsterSheet


class MonsterInstance(BaseInstance):
    """Dynamic monster state bound to a MonsterSheet template."""

    template_id: str

    # Template reference
    sheet: MonsterSheet

    # Runtime state
    state: EntityState

    # Location tracking
    current_location_id: str

    @property
    def display_name(self) -> str:
        """Human-readable name for UI/combat."""
        return self.sheet.name
