"""ScenarioInstance model representing dynamic scenario/progression state."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.types import JSONSerializable
from app.models.location import LocationState
from app.models.quest import Quest
from app.models.scenario import ScenarioSheet


class ScenarioInstance(BaseModel):
    """Dynamic scenario/progression state for a game session."""

    # Identity
    instance_id: str
    template_id: str  # scenario id
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Embedded scenario template
    sheet: ScenarioSheet

    # Progression (use sentinel "unknown-location" instead of None for type safety)
    current_location_id: str = "unknown-location"
    current_act_id: str | None = None

    # Location and quests state
    location_states: dict[str, LocationState] = Field(default_factory=dict)
    active_quests: list[Quest] = Field(default_factory=list)
    completed_quest_ids: list[str] = Field(default_factory=list)
    quest_flags: dict[str, JSONSerializable] = Field(default_factory=dict)

    # DM notes/tags
    notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = datetime.now()

    def is_in_known_location(self) -> bool:
        """Check if currently in a known/defined location."""
        return self.current_location_id != "unknown-location"
