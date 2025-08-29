"""Enhanced location models with state tracking."""

from enum import Enum

from pydantic import BaseModel, Field


class DangerLevel(str, Enum):
    """Danger level of a location."""

    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"
    CLEARED = "cleared"  # Was dangerous, now safe


class ConnectionRequirement(BaseModel):
    """Requirement to traverse a connection."""

    type: str  # "key", "quest", "skill_check", "combat", etc.
    description: str
    requirement_id: str | None = None  # Item ID for keys, quest ID for quests
    dc: int | None = None  # For skill checks
    is_met: bool = False


class LocationConnection(BaseModel):
    """Connection between locations."""

    to_location_id: str
    description: str  # "A dark tunnel leads north"
    direction: str | None = None  # "north", "south", etc.
    requirements: list[ConnectionRequirement] = Field(default_factory=list)
    is_visible: bool = True  # Can be hidden until discovered
    is_accessible: bool = True  # Can be blocked

    def can_traverse(self) -> bool:
        """Check if connection can be traversed."""
        if not self.is_accessible:
            return False
        return all(req.is_met for req in self.requirements)


class LootEntry(BaseModel):
    """Loot table entry for a location."""

    item_name: str  # Must match items.json
    quantity_min: int = 1
    quantity_max: int = 1
    probability: float = 1.0  # 0.0 to 1.0
    found: bool = False  # Track if already looted
    hidden: bool = False  # Requires search to find
    dc_to_find: int | None = None  # Investigation DC if hidden


class MonsterSpawn(BaseModel):
    """Monster spawn definition for encounters."""

    monster_name: str  # Must match monsters.json
    quantity_min: int = 1
    quantity_max: int = 1
    probability: float = 1.0  # Chance to appear


class LocationState(BaseModel):
    """Runtime state of a location."""

    location_id: str
    visited: bool = False
    times_visited: int = 0
    danger_level: DangerLevel = DangerLevel.MODERATE
    npcs_present: list[str] = Field(default_factory=list)  # NPC names currently here
    completed_encounters: list[str] = Field(default_factory=list)  # Encounter IDs completed
    discovered_secrets: list[str] = Field(default_factory=list)  # Secret IDs found
    looted_items: list[str] = Field(default_factory=list)  # Track which loot was taken
    active_effects: list[str] = Field(default_factory=list)  # Environmental effects
    notes: list[str] = Field(default_factory=list)  # DM notes about what happened here

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

    def add_npc(self, npc_name: str) -> None:
        """Add an NPC to this location."""
        if npc_name not in self.npcs_present:
            self.npcs_present.append(npc_name)

    def remove_npc(self, npc_name: str) -> None:
        """Remove an NPC from this location."""
        if npc_name in self.npcs_present:
            self.npcs_present.remove(npc_name)

    def get_description_variant(self) -> str:
        """Get description variant based on state."""
        if self.times_visited == 0:
            return "first_visit"
        elif self.danger_level == DangerLevel.CLEARED:
            return "cleared"
        else:
            return "return_visit"
