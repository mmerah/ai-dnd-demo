"""Monster sheet models for D&D 5e stat blocks."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.attributes import Abilities, AttackAction, SkillValue
from app.models.instances.entity_state import HitPoints


class MonsterSpecialAbility(BaseModel):
    """Special ability or trait for a monster."""

    name: str
    description: str


class MonsterSheet(BaseModel):
    """Minimal monster stat block (template)."""

    # Basic Information
    index: str
    name: str
    type: str
    size: str = Field(pattern="^(Tiny|Small|Medium|Large|Huge|Gargantuan)$")
    alignment: str

    # Combat Stats
    armor_class: int = Field(ge=1)
    hit_points: HitPoints
    hit_dice: str
    speed: str

    # Challenge Rating
    challenge_rating: float = Field(ge=0)

    # Abilities
    abilities: Abilities

    # Skills (optional)
    skills: list[SkillValue] = Field(default_factory=list)

    # Senses & Languages
    senses: str
    languages: list[str] = Field(default_factory=list)

    # Attacks
    attacks: list[AttackAction]

    # Special Abilities
    special_abilities: list[MonsterSpecialAbility] = Field(default_factory=list)

    # Damage Modifiers (optional)
    damage_vulnerabilities: list[str] = Field(default_factory=list)
    damage_resistances: list[str] = Field(default_factory=list)
    damage_immunities: list[str] = Field(default_factory=list)
    condition_immunities: list[str] = Field(default_factory=list)

    # Content pack this monster comes from
    content_pack: str

    def has_multiattack(self) -> bool:
        """Check if this monster has multiattack ability."""
        return any(ability.name.lower() == "multiattack" for ability in self.special_abilities)

    def get_multiattack_description(self) -> str | None:
        """Get multiattack description if available."""
        for ability in self.special_abilities:
            if ability.name.lower() == "multiattack":
                return ability.description
        return None

    @field_validator("languages", mode="before")
    @classmethod
    def _normalize_languages(cls, v: list[str] | str | None) -> list[str] | str | None:
        if v is None:
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p and p.strip().lower() != "none"]
            return [p.lower().replace(" ", "-") for p in parts]
        return v

    @field_validator("hit_points", mode="before")
    @classmethod
    def _normalize_hit_points(cls, v: int | dict[str, int] | HitPoints) -> dict[str, int] | HitPoints:
        if isinstance(v, int):
            return {"current": v, "maximum": v, "temporary": 0}
        return v
