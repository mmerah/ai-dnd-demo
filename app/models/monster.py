"""Monster sheet models for D&D 5e stat blocks.

Represents the static/template data for a monster. Runtime state belongs to
MonsterInstance (see app/models/instances/monster_instance.py).
"""

from pydantic import BaseModel, Field

from app.models.attributes import Abilities, AttackAction, SkillValue
from app.models.instances.entity_state import HitPoints


class MonsterSpecialAbility(BaseModel):
    """Special ability or trait for a monster."""

    name: str
    description: str


class MonsterSheet(BaseModel):
    """Minimal monster stat block (template)."""

    # Basic Information
    name: str
    type: str
    size: str = Field(pattern="^(Tiny|Small|Medium|Large|Huge|Gargantuan)$")
    alignment: str  # alignment index (e.g., 'neutral-evil', 'unaligned')

    # Optional stable index (preferred primary key if present)
    index: str | None = None

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
    languages: list[str] = Field(default_factory=list)  # language indexes

    # Attacks
    attacks: list[AttackAction]

    # Special Abilities
    special_abilities: list[MonsterSpecialAbility] = Field(default_factory=list)

    # Damage Modifiers (optional)
    damage_vulnerabilities: list[str] = Field(default_factory=list)
    damage_resistances: list[str] = Field(default_factory=list)
    damage_immunities: list[str] = Field(default_factory=list)
    condition_immunities: list[str] = Field(default_factory=list)

    def calculate_modifier(self, ability_score: int) -> int:
        """Calculate ability modifier from score."""
        return (ability_score - 10) // 2

    def get_initiative_modifier(self) -> int:
        """Get initiative modifier (DEX modifier)."""
        return self.calculate_modifier(self.abilities.DEX)

    def has_multiattack(self) -> bool:
        """Check if this monster has multiattack ability."""
        return any(ability.name.lower() == "multiattack" for ability in self.special_abilities)

    def get_multiattack_description(self) -> str | None:
        """Get multiattack description if available."""
        for ability in self.special_abilities:
            if ability.name.lower() == "multiattack":
                return ability.description
        return None
