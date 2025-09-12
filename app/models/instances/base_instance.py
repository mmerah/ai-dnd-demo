"""Base instance model for runtime entities that share common behavior."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.instances.entity_state import EntityState


class BaseInstance(BaseModel):
    """Abstract base for Character/NPC/Monster instances at runtime."""

    # Identity
    instance_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Dynamic runtime state
    state: EntityState

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now()

    def is_alive(self) -> bool:
        """Alive if current HP > 0."""
        return self.state.hit_points.current > 0

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name used across UI/combat."""
        raise NotImplementedError
