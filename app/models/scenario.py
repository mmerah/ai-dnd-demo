"""Scenario models for D&D adventure content."""

from pydantic import BaseModel, Field

from app.models.location import DangerLevel, EncounterParticipantSpawn, LocationConnection, LootEntry
from app.models.monster import MonsterSheet


class ScenarioMonster(BaseModel):
    """Notable monster defined by the scenario with embedded stat block."""

    id: str
    display_name: str
    description: str | None = None
    monster: MonsterSheet


class Encounter(BaseModel):
    """Encounter definition for a location."""

    id: str
    # Combat, Skill Challenge, Trap, Roleplay, Environmental, etc.
    type: str
    description: str
    difficulty: str
    participant_spawns: list[EncounterParticipantSpawn] = Field(default_factory=list)
    # For skill challenges/traps
    dc: int | None = None
    rewards: list[str] = Field(default_factory=list)


class Secret(BaseModel):
    """Hidden secret in a location."""

    id: str
    description: str
    # "search", "specific_action", "dialogue", etc.
    discovery_method: str
    # Investigation/Perception DC if applicable
    dc: int | None = None
    reward: str | None = None


class LocationDescriptions(BaseModel):
    """Multiple description variants for different states."""

    first_visit: str
    return_visit: str | None = None
    cleared: str | None = None
    # Conditional descriptions
    special_conditions: dict[str, str] = Field(default_factory=dict)


class ScenarioLocation(BaseModel):
    """Enhanced location within a scenario."""

    id: str
    name: str
    description: str
    descriptions: LocationDescriptions | None = None
    notable_monsters: list[ScenarioMonster] = Field(default_factory=list)
    encounter_ids: list[str] = Field(default_factory=list)
    monster_ids: list[str] = Field(default_factory=list)
    connections: list[LocationConnection] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    environmental_features: list[str] = Field(default_factory=list)
    secrets: list[Secret] = Field(default_factory=list)
    loot_table: list[LootEntry] = Field(default_factory=list)
    victory_conditions: list[str] = Field(default_factory=list)
    danger_level: DangerLevel = DangerLevel.MODERATE

    def get_description(self, variant: str = "default") -> str:
        """Get appropriate description based on state."""
        if not self.descriptions:
            return self.description

        if variant == "first_visit" and self.descriptions.first_visit:
            return self.descriptions.first_visit
        if variant == "return_visit" and self.descriptions.return_visit:
            return self.descriptions.return_visit
        if variant == "cleared" and self.descriptions.cleared:
            return self.descriptions.cleared
        if variant in self.descriptions.special_conditions:
            return self.descriptions.special_conditions[variant]

        return self.description


class ScenarioSheet(BaseModel):
    """Complete enhanced scenario/adventure definition."""

    id: str = Field(default="default")
    title: str
    description: str
    starting_location_id: str
    locations: list[ScenarioLocation]
    encounters: dict[str, Encounter] = Field(default_factory=dict)
    random_encounters: list[Encounter] = Field(default_factory=list)

    # Content packs used by this scenario
    content_packs: list[str] = Field(default_factory=lambda: ["srd"])

    def get_location(self, location_id: str) -> ScenarioLocation | None:
        """Get a location by ID."""
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        return None

    def get_starting_location(self) -> ScenarioLocation:
        """Get the starting location."""
        location = self.get_location(self.starting_location_id)
        if not location:
            raise ValueError(f"Starting location '{self.starting_location_id}' not found in scenario '{self.id}'")
        return location

    def get_encounter_by_id(self, encounter_id: str) -> Encounter | None:
        """Find an encounter by ID."""
        # Check the encounters dictionary
        if encounter_id in self.encounters:
            return self.encounters[encounter_id]

        # Also check random encounters
        for encounter in self.random_encounters:
            if encounter.id == encounter_id:
                return encounter

        return None

    def get_initial_narrative(self) -> str:
        """Generate initial narrative for scenario start."""
        # Keep formatting light to avoid biasing the AI's style.
        start_loc = self.get_starting_location()
        parts = [
            f"{self.title}",
            f"{self.description}",
            f"{start_loc.name}",
            start_loc.get_description("first_visit"),
        ]
        return "\n\n".join(parts)
