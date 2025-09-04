"""Character model for D&D 5e character sheet."""

from pydantic import BaseModel, Field

from app.models.ability import Abilities
from app.models.item import InventoryItem
from app.models.spell import Spellcasting


class CustomFeature(BaseModel):
    """Character feature or trait."""

    name: str
    description: str


class Currency(BaseModel):
    """Character wealth tracking."""

    copper: int = Field(ge=0, default=0)
    silver: int = Field(ge=0, default=0)
    electrum: int = Field(ge=0, default=0)
    gold: int = Field(ge=0, default=0)
    platinum: int = Field(ge=0, default=0)


class Personality(BaseModel):
    """Character personality traits for roleplay."""

    traits: list[str] = Field(default_factory=list)
    ideals: list[str] = Field(default_factory=list)
    bonds: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)


class CharacterSheet(BaseModel):
    """Character template for pre-game selection.

    Contains base identity and choices only. All dynamic/derived fields
    live on CharacterInstance at runtime.
    """

    # Basic Information
    id: str
    name: str
    race: str
    class_index: str
    subclass: str | None = None
    subrace: str | None = None
    # Initialization-only fields (for seeding instances)
    starting_level: int = Field(ge=1, le=20, default=1)
    background: str
    alignment: str
    starting_experience_points: int = Field(ge=0, default=0)

    # Ability Scores (initial seeds)
    starting_abilities: Abilities

    # Custom features (character-specific choices/customizations)
    custom_features: list[CustomFeature] = Field(default_factory=list)

    # SRD catalog references
    feature_indexes: list[str] = Field(default_factory=list)
    trait_indexes: list[str] = Field(default_factory=list)
    feat_indexes: list[str] = Field(default_factory=list)

    # Spellcasting seed (known/prepared)
    starting_spellcasting: Spellcasting | None = None

    # Inventory & Currency (initial seeds)
    starting_inventory: list[InventoryItem] = Field(default_factory=list)
    starting_currency: Currency

    # Personality & Background
    personality: Personality
    backstory: str
    languages: list[str]

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

    @property
    def class_display(self) -> str:
        """Human-readable class name derived from `class_index`.

        Falls back to formatting the index (e.g., "circle-of-the-moon" -> "Circle Of The Moon").
        """
        if not self.class_index:
            return ""
        # Replace dashes with spaces and title-case for display
        return self.class_index.replace("-", " ").title()
