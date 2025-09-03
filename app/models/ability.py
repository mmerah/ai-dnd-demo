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
