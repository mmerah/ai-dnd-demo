"""Ability score models for D&D 5e."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class EntityType(str, Enum):
    """Allowed runtime entity categories used in combat and lookups."""

    PLAYER = "player"
    NPC = "npc"
    MONSTER = "monster"


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
    attack_roll_bonus: int
    damage: str
    damage_type: str
    range: str = "melee"
    properties: list[str] = Field(default_factory=list)
    # Extra optional fields commonly used by monster actions
    type: str = "Melee"
    reach: str = "5 ft."
    special: str = ""

    @field_validator("type", mode="before")
    @classmethod
    def _default_type(cls, v: str | None) -> str:
        return v or "Melee"

    @field_validator("range", mode="before")
    @classmethod
    def _normalize_range(cls, v: str | None, info: ValidationInfo) -> str:
        if v is None or v == "":
            atk_type: str | None
            # info.data contains raw input prior to validation
            try:
                data = info.data or {}
                atk_type = data.get("type") if isinstance(data, dict) else None
            except Exception:
                atk_type = None
            if (atk_type or "Melee").lower() == "melee":
                return "melee"
            return "ranged"
        return v

    @field_validator("reach", mode="before")
    @classmethod
    def _normalize_reach(cls, v: str | None) -> str:
        return v or "5 ft."

    @field_validator("special", mode="before")
    @classmethod
    def _normalize_special(cls, v: str | None) -> str:
        return v or ""

    @field_validator("properties", mode="before")
    @classmethod
    def _normalize_properties(cls, v: Any) -> list[str]:
        return v or []

    @field_validator("damage", mode="before")
    @classmethod
    def _normalize_damage(cls, v: str | None) -> str:
        return "" if v is None else v


class SkillValue(BaseModel):
    """Runtime skill value bound to a skill index."""

    index: str
    value: int
