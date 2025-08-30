"""Spell models for D&D 5e spellcasting system."""

from enum import Enum

from pydantic import BaseModel, Field


class SpellSchool(str, Enum):
    """D&D 5e spell schools."""

    ABJURATION = "Abjuration"
    CONJURATION = "Conjuration"
    DIVINATION = "Divination"
    ENCHANTMENT = "Enchantment"
    EVOCATION = "Evocation"
    ILLUSION = "Illusion"
    NECROMANCY = "Necromancy"
    TRANSMUTATION = "Transmutation"


class SpellDefinition(BaseModel):
    """Definition of a spell from data files."""

    name: str
    level: int = Field(ge=0, le=9)  # 0 = cantrip, 1-9 = spell levels
    school: SpellSchool
    casting_time: str  # e.g., "1 action", "1 bonus action", "1 minute"
    range: str  # e.g., "Touch", "30 feet", "Self"
    components: str  # e.g., "V, S, M (a pinch of sand)"
    duration: str  # e.g., "Instantaneous", "Concentration, up to 1 minute"
    description: str
    higher_levels: str | None = None  # Description of effects at higher levels
    classes: list[str]  # List of classes that can cast this spell
    ritual: bool = False  # Whether the spell can be cast as a ritual
    concentration: bool = False  # Whether the spell requires concentration

    @property
    def is_cantrip(self) -> bool:
        """Check if this is a cantrip."""
        return self.level == 0

    def can_be_cast_by_class(self, class_name: str) -> bool:
        """Check if a specific class can cast this spell."""
        return class_name in self.classes or class_name.lower() in [c.lower() for c in self.classes]


class SpellSlot(BaseModel):
    """Spell slot tracking for a spell level."""

    level: int = Field(ge=1, le=9)
    total: int = Field(ge=0)
    current: int = Field(ge=0)

    def model_post_init(self, __context: object) -> None:
        """Validate current slots don't exceed total after initialization."""
        if self.current > self.total:
            raise ValueError(f"Current spell slots ({self.current}) cannot exceed total ({self.total})")

    def use_slot(self) -> bool:
        """Use a spell slot. Returns True if successful, False if no slots available."""
        if self.current > 0:
            self.current -= 1
            return True
        return False

    def restore_slot(self, amount: int = 1) -> int:
        """Restore spell slots. Returns number of slots actually restored."""
        restored = min(amount, self.total - self.current)
        self.current += restored
        return restored

    def restore_all(self) -> None:
        """Restore all spell slots to maximum."""
        self.current = self.total


class SpellcastingAbility(str, Enum):
    """Spellcasting ability scores."""

    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    CHARISMA = "Charisma"
    # Short forms
    INT = "INT"
    WIS = "WIS"
    CHA = "CHA"


class Spellcasting(BaseModel):
    """Character spellcasting information."""

    ability: SpellcastingAbility
    spell_save_dc: int = Field(ge=1)
    spell_attack_bonus: int
    spells_known: list[str]  # List of spell names
    spell_slots: dict[int, SpellSlot]  # Key is spell level (1-9)

    # Optional tracking
    spells_prepared: list[str] = Field(default_factory=list)  # For prepared casters
    ritual_spells: list[str] = Field(default_factory=list)  # Known ritual spells

    def get_slot(self, level: int) -> SpellSlot | None:
        """Get spell slot for a specific level."""
        return self.spell_slots.get(level)

    def can_cast_spell(self, spell_name: str, level: int) -> bool:
        """Check if character can cast a spell at a given level."""
        if spell_name not in self.spells_known:
            return False

        slot = self.get_slot(level)
        return slot is not None and slot.current > 0

    def use_spell_slot(self, level: int) -> bool:
        """Use a spell slot of the given level. Returns True if successful."""
        slot = self.get_slot(level)
        if slot:
            return slot.use_slot()
        return False

    def restore_all_slots(self) -> None:
        """Restore all spell slots (for long rest)."""
        for slot in self.spell_slots.values():
            slot.restore_all()
