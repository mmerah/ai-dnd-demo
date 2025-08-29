"""NPC and Monster models for D&D 5e."""

from pydantic import BaseModel, Field

from app.models.character import Abilities, HitPoints


class NPCAttack(BaseModel):
    """NPC/Monster attack action."""

    name: str
    type: str = Field(pattern="^(Melee|Ranged|Melee or Ranged)$")
    to_hit: int
    reach: str | None = None
    range: str | None = None
    damage: str
    damage_type: str
    special: str | None = None


class SpecialAbility(BaseModel):
    """Special ability or trait for NPC/Monster."""

    name: str
    description: str


class NPCSheet(BaseModel):
    """Minimal NPC/Monster stat block."""

    # Basic Information
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
    skills: dict[str, int] = Field(default_factory=dict)

    # Senses & Languages
    senses: str
    languages: str | None = None

    # Attacks
    attacks: list[NPCAttack]

    # Special Abilities
    special_abilities: list[SpecialAbility] = Field(default_factory=list)

    # Damage Modifiers (optional)
    damage_vulnerabilities: list[str] = Field(default_factory=list)
    damage_resistances: list[str] = Field(default_factory=list)
    damage_immunities: list[str] = Field(default_factory=list)
    condition_immunities: list[str] = Field(default_factory=list)

    # Runtime state
    conditions: list[str] = Field(default_factory=list)

    def calculate_modifier(self, ability_score: int) -> int:
        """Calculate ability modifier from score."""
        return (ability_score - 10) // 2

    def take_damage(self, amount: int) -> int:
        """Apply damage to NPC, returns actual damage taken."""
        actual_damage = min(amount, self.hit_points.current)
        self.hit_points.current -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal NPC, returns actual healing done."""
        actual_healing = min(amount, self.hit_points.maximum - self.hit_points.current)
        self.hit_points.current += actual_healing
        return actual_healing

    def add_condition(self, condition: str) -> None:
        """Add a condition to the NPC."""
        if condition not in self.conditions:
            self.conditions.append(condition)

    def remove_condition(self, condition: str) -> None:
        """Remove a condition from the NPC."""
        if condition in self.conditions:
            self.conditions.remove(condition)

    def is_alive(self) -> bool:
        """Check if NPC is still alive."""
        return self.hit_points.current > 0

    def get_initiative_modifier(self) -> int:
        """Get initiative modifier (DEX modifier)."""
        return self.calculate_modifier(self.abilities.DEX)

    def has_multiattack(self) -> bool:
        """Check if this NPC has multiattack ability."""
        return any(ability.name.lower() == "multiattack" for ability in self.special_abilities)

    def get_multiattack_description(self) -> str | None:
        """Get multiattack description if available."""
        for ability in self.special_abilities:
            if ability.name.lower() == "multiattack":
                return ability.description
        return None
