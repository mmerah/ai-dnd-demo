"""NPCInstance model representing a scenario NPC materialized for a game."""

from __future__ import annotations

from pydantic import Field

from app.models.instances.base_instance import BaseInstance
from app.models.instances.entity_state import EntityState
from app.models.memory import MemoryEntry
from app.models.npc import NPCImportance, NPCSheet


class NPCInstance(BaseInstance):
    """Dynamic NPC state."""

    scenario_npc_id: str  # id from scenario template (stable)

    # Template reference
    sheet: NPCSheet

    # Runtime location and state
    current_location_id: str
    attitude: str | None = None
    npc_memories: list[MemoryEntry] = Field(default_factory=list)

    # Dynamic character state (mirrors CharacterInstance.state)
    state: EntityState

    @property
    def display_name(self) -> str:
        """Human-readable name for UI/combat."""
        return self.sheet.character.name

    @property
    def importance(self) -> NPCImportance:
        """Proxy importance from NPC sheet (major vs minor)."""
        return self.sheet.importance
