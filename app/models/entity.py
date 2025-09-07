"""Unified entity protocol for runtime operations.

Defines a minimal interface that runtime entities (player character,
NPCs, and monsters) implement so systems can treat them uniformly
for all operations (combat, HP updates, conditions, inventory, etc).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.instances.entity_state import EntityState


@runtime_checkable
class IEntity(Protocol):
    """Protocol that character, NPC, and monster instances implement for all runtime operations."""

    @property
    def instance_id(self) -> str:  # stable per save
        ...

    @property
    def display_name(self) -> str:  # human-readable name for UI
        ...

    @property
    def state(self) -> EntityState:  # dynamic runtime state
        ...

    def is_alive(self) -> bool:  # shared life check
        ...
