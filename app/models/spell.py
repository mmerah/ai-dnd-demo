"""Spell models for D&D 5e spellcasting system."""

from enum import Enum
from typing import Optional, Union

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


class SpellAreaOfEffect(BaseModel):
    size: int
    type: str


class SpellDC(BaseModel):
    dc_type: str  # index for ability score (e.g., "wis", "dex")
    dc_success: str | None = None  # e.g., "half"


class SpellDefinition(BaseModel):
    """Definition of a spell from data files (SRD-aligned)."""

    # Identity
    index: str
    name: str

    # Core
    level: int = Field(ge=0, le=9)  # 0 = cantrip, 1-9 = spell levels
    school: str  # magic school index (e.g., "evocation")
    casting_time: str  # e.g., "1 action", "1 bonus action", "1 minute"
    range: str  # e.g., "Touch", "30 feet", "Self"
    duration: str  # e.g., "Instantaneous", "Concentration, up to 1 minute"
    description: str
    higher_levels: Optional[str] = None  # Description of effects at higher levels

    # Components
    components_list: list[str] = Field(default_factory=list)
    material: Optional[str] = None

    # Flags
    ritual: bool = False
    concentration: bool = False

    # References
    classes: list[str] = Field(default_factory=list)  # class indexes
    subclasses: list[str] = Field(default_factory=list)  # subclass indexes

    # Optional mechanics
    area_of_effect: Optional[SpellAreaOfEffect] = None
    attack_type: Optional[str] = None
    dc: Optional[SpellDC] = None
    damage_at_slot_level: Optional[dict[int, Union[str, int]]] = None
    heal_at_slot_level: Optional[dict[int, Union[str, int]]] = None
    damage_at_character_level: Optional[dict[int, Union[str, int]]] = None

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
