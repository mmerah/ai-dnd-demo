from pydantic import BaseModel, Field


class BackgroundOption(BaseModel):
    """A personality option (ideal) with optional alignment associations."""

    text: str
    alignments: list[str] = Field(default_factory=list)


class BackgroundFeature(BaseModel):
    """Background-specific feature or ability."""

    name: str
    description: str


class BackgroundDefinition(BaseModel):
    """D&D 5e character background definition."""

    # Identity
    index: str
    name: str
    description: str

    # Feature
    feature: BackgroundFeature | None = None

    # Proficiencies
    skill_proficiencies: list[str] = Field(
        default_factory=list,
        description="Skill indexes granted by this background (e.g., ['insight', 'religion'])",
    )
    tool_proficiencies: list[str] = Field(
        default_factory=list,
        description="Tool proficiency indexes granted (e.g., ['thieves-tools'])",
    )
    language_count: int = Field(
        default=0,
        ge=0,
        description="Number of languages the character can choose",
    )

    # Equipment. Only description for now
    starting_equipment_description: str | None = Field(
        default=None,
        description="Summary of starting equipment provided",
    )

    # Personality scaffolding
    personality_trait_options: list[str] = Field(
        default_factory=list,
        description="8 personality trait options (player chooses 2)",
    )
    ideal_options: list[BackgroundOption] = Field(
        default_factory=list,
        description="6 ideal options with alignment associations (player chooses 1)",
    )
    bond_options: list[str] = Field(
        default_factory=list,
        description="6 bond options (player chooses 1)",
    )
    flaw_options: list[str] = Field(
        default_factory=list,
        description="6 flaw options (player chooses 1)",
    )

    # Content pack metadata
    content_pack: str
