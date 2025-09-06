"""Shared dynamic entity state for characters and NPCs (DRY)."""

from pydantic import BaseModel, Field

from app.models.attributes import Abilities, AttackAction, SavingThrows, SkillValue
from app.models.character import Currency
from app.models.item import InventoryItem
from app.models.spell import Spellcasting


class HitPoints(BaseModel):
    current: int
    maximum: int
    temporary: int | None = None


class HitDice(BaseModel):
    total: int
    current: int | None = None
    type: str


class EntityState(BaseModel):
    abilities: Abilities
    level: int = Field(ge=1, le=20, default=1)
    experience_points: int = Field(ge=0, default=0)
    hit_points: HitPoints
    hit_dice: HitDice
    armor_class: int = Field(ge=1, default=10)
    initiative: int = 0
    speed: int = Field(ge=0, default=30)
    saving_throws: SavingThrows = Field(default_factory=SavingThrows)
    skills: list[SkillValue] = Field(default_factory=list)
    attacks: list[AttackAction] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    exhaustion_level: int = Field(ge=0, le=6, default=0)
    inspiration: bool = False
    inventory: list[InventoryItem] = Field(default_factory=list)
    currency: Currency
    spellcasting: Spellcasting | None = None
