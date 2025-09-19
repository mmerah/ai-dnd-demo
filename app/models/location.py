"""Enhanced location models with state tracking."""

from enum import Enum

from pydantic import BaseModel, Field

from app.models.attributes import EntityType
from app.models.memory import MemoryEntry


class DangerLevel(str, Enum):
    """Danger level of a location."""

    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"
    CLEARED = "cleared"


class ConnectionRequirement(BaseModel):
    """Requirement to traverse a connection."""

    type: str
    description: str
    # Item ID for keys, quest ID for quests
    requirement_id: str | None = None
    # Skill checks
    dc: int | None = None
    is_met: bool = False


class LocationConnection(BaseModel):
    """Connection between locations."""

    to_location_id: str
    description: str
    direction: str | None = None
    requirements: list[ConnectionRequirement] = Field(default_factory=list)
    is_visible: bool = True
    is_accessible: bool = True

    def can_traverse(self) -> bool:
        """Check if connection can be traversed."""
        if not self.is_accessible:
            return False
        return all(req.is_met for req in self.requirements)


class LootEntry(BaseModel):
    """Loot table entry for a location."""

    item_index: str
    quantity_min: int = 1
    quantity_max: int = 1
    probability: float = 1.0
    found: bool = False
    hidden: bool = False
    dc_to_find: int | None = None


class SpawnType(str, Enum):
    """Type of entity to spawn. Repository is data/monsters, scenario data/scenarios/{id}/monsters."""

    REPOSITORY = "repository"
    SCENARIO = "scenario"


class EncounterParticipantSpawn(BaseModel):
    """Participant spawn definition for encounters (monsters or NPCs)."""

    entity_type: EntityType
    spawn_type: SpawnType
    entity_id: str
    quantity_min: int = 1
    quantity_max: int = 1
    probability: float = 1.0


class LocationState(BaseModel):
    """Runtime state of a location."""

    location_id: str
    visited: bool = False
    times_visited: int = 0
    danger_level: DangerLevel = DangerLevel.MODERATE
    completed_encounters: list[str] = Field(default_factory=list)
    discovered_secrets: list[str] = Field(default_factory=list)
    looted_items: list[str] = Field(default_factory=list)
    active_effects: list[str] = Field(default_factory=list)
    location_memories: list[MemoryEntry] = Field(default_factory=list)

    def mark_visited(self) -> None:
        """Mark location as visited."""
        self.visited = True
        self.times_visited += 1

    def complete_encounter(self, encounter_id: str) -> None:
        """Mark an encounter as completed."""
        if encounter_id not in self.completed_encounters:
            self.completed_encounters.append(encounter_id)

    def discover_secret(self, secret_id: str) -> None:
        """Mark a secret as discovered."""
        if secret_id not in self.discovered_secrets:
            self.discovered_secrets.append(secret_id)
