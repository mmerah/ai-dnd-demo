"""ScenarioInstance model representing dynamic scenario/location state."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.location import LocationState
from app.models.memory import MemoryEntry
from app.models.scenario import ScenarioSheet


class ScenarioInstance(BaseModel):
    """Dynamic scenario/location state for a game session."""

    # Identity
    instance_id: str
    template_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Embedded scenario template
    sheet: ScenarioSheet

    # Current location. Use sentinel "unknown-location" instead of None
    current_location_id: str = "unknown-location"

    # Location state
    location_states: dict[str, LocationState] = Field(default_factory=dict)

    # Structured memory system
    world_memories: list[MemoryEntry] = Field(default_factory=list)
    last_world_message_index: int = -1
    last_location_message_index: dict[str, int] = Field(default_factory=dict)
    last_npc_message_index: dict[str, int] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = datetime.now()

    def is_in_known_location(self) -> bool:
        """Check if currently in a known/defined location."""
        return self.current_location_id != "unknown-location"
