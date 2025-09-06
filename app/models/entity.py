"""Unified entity protocol for combat and runtime operations.

Defines a minimal interface that runtime entities (player character,
NPCs, and monsters) implement so systems like combat can treat them
uniformly.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from app.models.instances.entity_state import EntityState


class EntityType(str, Enum):
    """Allowed runtime entity categories used in combat and lookups."""

    PLAYER = "player"
    NPC = "npc"
    MONSTER = "monster"


@runtime_checkable
class ICombatEntity(Protocol):
    """Protocol that character, NPC, and monster instances implement."""

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
