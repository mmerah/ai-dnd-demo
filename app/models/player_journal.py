"""Player journal entries for personal note-taking."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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
    pinned: bool = Field(default=False, description="Whether this entry is pinned to the top of the list")

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_and_validate_tags(cls, tags: list[str]) -> list[str]:
        """Normalize and validate tag format and length.

        Normalization:
        - Convert to lowercase
        - Replace spaces with dashes
        - Strip whitespace

        Validation:
        - Max 50 tags
        - Each tag max 50 characters
        - Only alphanumeric, dash, underscore, colon
        """
        if len(tags) > 50:
            raise ValueError("Too many tags (max 50)")

        normalized = []
        for tag in tags:
            # Strip and skip empty tags
            clean = tag.strip()
            if not clean:
                continue

            # Normalize: lowercase and replace spaces with dashes
            clean = clean.lower().replace(" ", "-")

            # Validate length
            if len(clean) > 50:
                raise ValueError(f"Tag too long (max 50 characters): {tag}")

            # Validate format
            if not re.match(r"^[a-z0-9_:-]+$", clean):
                raise ValueError(f"Invalid tag format (only letters, numbers, dash, underscore, colon allowed): {tag}")

            normalized.append(clean)

        return normalized

    def touch(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now()
