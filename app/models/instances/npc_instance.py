"""NPCInstance model representing a scenario NPC materialized for a game."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.instances.entity_state import EntityState
from app.models.npc import NPCSheet


class NPCInstance(BaseModel):
    """Dynamic NPC state."""

    # Identity
    instance_id: str
    scenario_npc_id: str  # id from scenario template (stable)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Template reference
    sheet: NPCSheet

    # Runtime location and state
    current_location_id: str
    attitude: str | None = None
    notes: list[str] = Field(default_factory=list)

    # Dynamic character state (mirrors CharacterInstance.state)
    state: EntityState

    def touch(self) -> None:
        self.updated_at = datetime.now()

    def is_alive(self) -> bool:
        """NPC considered alive if embedded character has HP > 0."""
        return self.state.hit_points.current > 0

    @property
    def display_name(self) -> str:
        """Human-readable name for UI/combat."""
        return self.sheet.character.name
