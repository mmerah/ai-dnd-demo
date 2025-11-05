"""Structured memory entries for dynamic narrative recall."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MemorySource(str, Enum):
    """Scope of a recorded memory."""

    LOCATION = "location"
    NPC = "npc"
    WORLD = "world"


class MemoryEventKind(str, Enum):
    """Well-known triggers for world memories."""

    LOCATION_CLEARED = "location_cleared"
    ENCOUNTER_COMPLETED = "encounter_completed"


class WorldEventContext(BaseModel):
    """Structured metadata associated with a world memory."""

    location_id: str | None = None
    encounter_id: str | None = None
    npc_ids: list[str] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    """Append-only memory snapshot summarizing recent events."""

    created_at: datetime = Field(default_factory=datetime.now)
    source: MemorySource
    summary: str
    tags: list[str] = Field(default_factory=list)
    location_id: str | None = None
    npc_ids: list[str] = Field(default_factory=list)
    encounter_id: str | None = None
    since_timestamp: datetime | None = None
    since_message_index: int | None = None
