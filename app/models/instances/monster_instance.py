"""MonsterInstance model representing a runtime monster in the game.

Separates static template data (MonsterSheet) from mutable runtime state (EntityState),
aligned with CharacterInstance and NPCInstance patterns.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.instances.entity_state import EntityState
from app.models.monster import MonsterSheet


class MonsterInstance(BaseModel):
    """Dynamic monster state bound to a MonsterSheet template."""

    # Identity
    instance_id: str
    # Optional references for provenance
    template_id: str | None = None  # for scenario monsters
    repository_name: str | None = None  # for repository monsters
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Template reference
    sheet: MonsterSheet

    # Runtime state
    state: EntityState

    # Location tracking
    current_location_id: str

    def touch(self) -> None:
        self.updated_at = datetime.now()

    def is_alive(self) -> bool:
        return self.state.hit_points.current > 0

    @property
    def display_name(self) -> str:
        """Human-readable name for UI/combat."""
        return self.sheet.name
