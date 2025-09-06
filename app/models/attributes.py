"""Ability score models for D&D 5e."""

from pydantic import BaseModel, Field


class Abilities(BaseModel):
    """Character ability scores."""

    STR: int = Field(ge=1, le=30)
    DEX: int = Field(ge=1, le=30)
    CON: int = Field(ge=1, le=30)
    INT: int = Field(ge=1, le=30)
    WIS: int = Field(ge=1, le=30)
    CHA: int = Field(ge=1, le=30)


class AbilityModifiers(BaseModel):
    """Calculated ability modifiers."""

    STR: int
    DEX: int
    CON: int
    INT: int
    WIS: int
    CHA: int


class AbilityBonuses(BaseModel):
    """Ability score bonuses for races and subraces.

    All fields are optional with default 0.
    """

    STR: int = Field(default=0)
    DEX: int = Field(default=0)
    CON: int = Field(default=0)
    INT: int = Field(default=0)
    WIS: int = Field(default=0)
    CHA: int = Field(default=0)


class SavingThrows(BaseModel):
    """Saving throw modifiers by ability."""

    STR: int = 0
    DEX: int = 0
    CON: int = 0
    INT: int = 0
    WIS: int = 0
    CHA: int = 0


class AttackAction(BaseModel):
    name: str
    attack_roll_bonus: int | None = None
    damage: str | None = None
    damage_type: str | None = None
    range: str | None = None
    properties: list[str] = Field(default_factory=list)
    # Extra optional fields commonly used by monster actions
    type: str | None = None  # e.g., "Melee", "Ranged", "Melee or Ranged"
    reach: str | None = None  # e.g., "5 ft.", "10 ft."
    special: str | None = None  # additional notes


class SkillValue(BaseModel):
    """Runtime skill value bound to a skill index."""

    index: str
    value: int
