"""Scenario models for D&D adventure content."""

from pydantic import BaseModel, Field


class DialogueHint(BaseModel):
    """NPC dialogue hint."""

    text: str


class ScenarioNPC(BaseModel):
    """NPC definition within a scenario location."""

    name: str
    role: str
    description: str
    dialogue_hints: list[str] = Field(default_factory=list)


class Encounter(BaseModel):
    """Encounter definition for a location."""

    type: str  # Combat, Skill Challenge, Trap, etc.
    description: str
    difficulty: str | None = None  # Easy, Medium, Hard


class ScenarioLocation(BaseModel):
    """Location within a scenario."""

    id: str
    name: str
    description: str
    npcs: list[ScenarioNPC] = Field(default_factory=list)
    encounters: list[Encounter] = Field(default_factory=list)
    connections: list[str] = Field(default_factory=list)  # Connected location IDs
    events: list[str] = Field(default_factory=list)
    environmental_features: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    loot: list[str] = Field(default_factory=list)
    victory_conditions: list[str] = Field(default_factory=list)


class ScenarioAct(BaseModel):
    """Act/Chapter in scenario progression."""

    name: str
    locations: list[str]  # Location IDs
    objectives: list[str]


class ScenarioProgression(BaseModel):
    """Scenario progression structure."""

    act1: ScenarioAct
    act2: ScenarioAct
    act3: ScenarioAct
    act4: ScenarioAct | None = None


class TreasureGuidelines(BaseModel):
    """Guidelines for treasure distribution."""

    total_gold: str
    magic_items: str
    consumables: str
    mundane_items: str


class Scenario(BaseModel):
    """Complete scenario/adventure definition."""

    id: str = Field(default="default")
    title: str
    description: str
    starting_location: str  # Location ID
    locations: list[ScenarioLocation]
    progression: ScenarioProgression
    random_encounters: list[str] = Field(default_factory=list)
    treasure_guidelines: TreasureGuidelines

    def get_location(self, location_id: str) -> ScenarioLocation | None:
        """Get a location by ID."""
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        return None

    def get_starting_location(self) -> ScenarioLocation | None:
        """Get the starting location."""
        return self.get_location(self.starting_location)

    def get_initial_narrative(self) -> str:
        """Generate initial narrative for scenario start."""
        start_loc = self.get_starting_location()
        if not start_loc:
            return f"Your adventure '{self.title}' begins..."

        narrative = f"## {self.title}\n\n{self.description}\n\n"
        narrative += f"### {start_loc.name}\n\n{start_loc.description}"

        if start_loc.npcs:
            narrative += "\n\nYou notice several people here:"
            for npc in start_loc.npcs:
                narrative += f"\n- {npc.description}"

        return narrative
