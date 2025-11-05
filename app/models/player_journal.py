"""Player journal entries for personal note-taking."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlayerJournalEntry(BaseModel):
    """Player-created journal entry with tags and timestamps.

    Player journal entries are editable notes that complement the auto-generated
    memory system (world/location/NPC memories). They support manual and auto-linked
    tags for filtering and organization.
    """

    entry_id: str = Field(..., description="Unique identifier for the journal entry")
    created_at: datetime = Field(default_factory=datetime.now, description="Entry creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last modification timestamp")
    content: str = Field(..., min_length=1, max_length=10000, description="Journal entry text content")
    tags: list[str] = Field(default_factory=list, max_length=50, description="User-defined and auto-linked tags")
    location_id: str | None = Field(None, description="Auto-linked location ID at time of creation")
    npc_ids: list[str] = Field(default_factory=list, description="Auto-linked NPC IDs if dialogue active")

    def touch(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now()
