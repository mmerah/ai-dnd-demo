"""Character model for D&D 5e character sheet."""

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.models.ability import Abilities, AbilityModifiers
from app.models.item import InventoryItem
from app.models.spell import Spellcasting


class HitPoints(BaseModel):
    """Character hit point tracking."""

    current: int = Field(ge=0)
    maximum: int = Field(ge=1)
    temporary: int = Field(ge=0, default=0)

    @field_validator("current")
    @classmethod
    def validate_current_hp(cls, v: int, info: ValidationInfo) -> int:
        """Ensure current HP doesn't exceed maximum."""
        if "maximum" in info.data and v > info.data["maximum"]:
            raise ValueError(f"Current HP ({v}) cannot exceed maximum HP ({info.data['maximum']})")
        return v


class HitDice(BaseModel):
    """Hit dice for resting mechanics."""

    total: int = Field(ge=1)
    current: int = Field(ge=0)
    type: str = Field(pattern=r"^d(4|6|8|10|12|20)$")

    @field_validator("current")
    @classmethod
    def validate_current_dice(cls, v: int, info: ValidationInfo) -> int:
        """Ensure current dice don't exceed total."""
        if "total" in info.data and v > info.data["total"]:
            raise ValueError(f"Current hit dice ({v}) cannot exceed total ({info.data['total']})")
        return v


class Attack(BaseModel):
    """Character weapon attack."""

    name: str
    to_hit: int
    damage: str = Field(pattern=r"^\d+d\d+(\+\d+)?$")
    damage_type: str
    range: str | None = None
    properties: list[str] = Field(default_factory=list)


class Feature(BaseModel):
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
    """Complete D&D 5e character sheet."""

    # Basic Information
    id: str
    name: str
    race: str
    class_index: str
    subclass: str | None = None
    subrace: str | None = None
    level: int = Field(ge=1, le=20)
    background: str
    alignment: str
    experience_points: int = Field(ge=0, default=0)

    # Ability Scores
    abilities: Abilities
    ability_modifiers: AbilityModifiers

    # Combat Stats
    proficiency_bonus: int = Field(ge=2, le=6)
    armor_class: int = Field(ge=1)
    initiative: int
    speed: int = Field(ge=0)
    hit_points: HitPoints
    hit_dice: HitDice

    # Saving Throws & Skills
    saving_throws: dict[str, int]
    skills: dict[str, int]

    # Attacks
    attacks: list[Attack]

    # Custom features (character-specific choices/customizations)
    custom_features: list[Feature] = Field(default_factory=list)

    # SRD catalog references
    feature_indexes: list[str] = Field(default_factory=list)
    trait_indexes: list[str] = Field(default_factory=list)
    feat_indexes: list[str] = Field(default_factory=list)

    # Spellcasting (optional)
    spellcasting: Spellcasting | None = None

    # Inventory & Currency
    inventory: list[InventoryItem] = Field(default_factory=list)
    currency: Currency

    # Personality & Background
    personality: Personality
    backstory: str
    languages: list[str]

    # Status
    conditions: list[str] = Field(default_factory=list)
    exhaustion_level: int = Field(ge=0, le=6, default=0)
    inspiration: bool = False

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    @property
    def class_display(self) -> str:
        """Human-readable class name derived from `class_index`.

        Falls back to formatting the index (e.g., "circle-of-the-moon" -> "Circle Of The Moon").
        """
        if not self.class_index:
            return ""
        # Replace dashes with spaces and title-case for display
        return self.class_index.replace("-", " ").title()

    def calculate_modifier(self, ability_score: int) -> int:
        """Calculate ability modifier from score."""
        return (ability_score - 10) // 2

    def add_condition(self, condition: str) -> None:
        """Add a condition to the character."""
        if condition not in self.conditions:
            self.conditions.append(condition)

    def remove_condition(self, condition: str) -> None:
        """Remove a condition from the character."""
        if condition in self.conditions:
            self.conditions.remove(condition)

    def take_damage(self, amount: int) -> int:
        """Apply damage to character, returns actual damage taken."""
        # First reduce temporary HP
        if self.hit_points.temporary > 0:
            if amount <= self.hit_points.temporary:
                self.hit_points.temporary -= amount
                return 0
            amount -= self.hit_points.temporary
            self.hit_points.temporary = 0

        # Then reduce actual HP
        actual_damage = min(amount, self.hit_points.current)
        self.hit_points.current -= actual_damage
        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal character, returns actual healing done."""
        actual_healing = min(amount, self.hit_points.maximum - self.hit_points.current)
        self.hit_points.current += actual_healing
        return actual_healing

    def short_rest(self) -> dict[str, int]:
        """Perform a short rest, returns HP healed."""
        # Use hit dice to heal
        dice_used = 0
        hp_healed = 0
        # This is a simplified version - actual implementation would roll dice
        # For now, we'll just restore some HP based on available hit dice
        if self.hit_dice.current > 0:
            # Simplified: use one hit die and add CON modifier
            self.hit_dice.current -= 1
            dice_used = 1
            # Average roll plus CON modifier
            con_mod = self.ability_modifiers.CON
            healing = 6 + con_mod  # Assuming d10 hit die average
            hp_healed = self.heal(healing)

        return {"dice_used": dice_used, "hp_healed": hp_healed}

    def long_rest(self) -> None:
        """Perform a long rest."""
        # Restore all HP
        self.hit_points.current = self.hit_points.maximum
        self.hit_points.temporary = 0

        # Restore half of max hit dice (minimum 1)
        dice_to_restore = max(1, self.hit_dice.total // 2)
        self.hit_dice.current = min(self.hit_dice.total, self.hit_dice.current + dice_to_restore)

        # Restore all spell slots
        if self.spellcasting:
            self.spellcasting.restore_all_slots()

        # Remove exhaustion (one level)
        if self.exhaustion_level > 0:
            self.exhaustion_level -= 1
