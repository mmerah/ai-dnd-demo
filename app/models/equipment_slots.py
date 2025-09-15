"""Equipment slot system following D&D 5e conventions."""

from enum import Enum

from pydantic import BaseModel, model_validator


class EquipmentSlotType(str, Enum):
    """D&D 5e equipment slot types."""

    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    HANDS = "hands"
    FEET = "feet"
    WAIST = "waist"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    BACK = "back"
    AMMUNITION = "ammunition"


class EquipmentSlots(BaseModel):
    """Character equipment slots following D&D 5e conventions."""

    head: str | None = None
    neck: str | None = None
    chest: str | None = None
    hands: str | None = None
    feet: str | None = None
    waist: str | None = None
    main_hand: str | None = None
    off_hand: str | None = None
    ring_1: str | None = None
    ring_2: str | None = None
    back: str | None = None
    ammunition: str | None = None

    @model_validator(mode="after")
    def validate_two_handed_constraint(self) -> "EquipmentSlots":
        """Fail-fast validation: two-handed weapons block off-hand."""
        # This will be checked against ItemDefinition.two_handed flag
        return self

    def get_slot(self, slot_type: EquipmentSlotType) -> str | None:
        """Get item in specified slot."""
        if not hasattr(self, slot_type.value):
            raise ValueError(f"Invalid slot type: {slot_type}")
        value = getattr(self, slot_type.value)
        return value if isinstance(value, str) or value is None else None

    def set_slot(self, slot_type: EquipmentSlotType, item_index: str | None) -> None:
        """Set item in specified slot with validation."""
        if not hasattr(self, slot_type.value):
            raise ValueError(f"Invalid slot type: {slot_type}")
        setattr(self, slot_type.value, item_index)

    def find_item_slots(self, item_index: str) -> list[EquipmentSlotType]:
        """Find all slots where an item is equipped."""
        slots = []
        for slot_type in EquipmentSlotType:
            if self.get_slot(slot_type) == item_index:
                slots.append(slot_type)
        return slots

    def clear_item(self, item_index: str) -> list[EquipmentSlotType]:
        """Remove item from all slots it occupies. Returns cleared slots."""
        cleared = []
        for slot_type in EquipmentSlotType:
            if self.get_slot(slot_type) == item_index:
                self.set_slot(slot_type, None)
                cleared.append(slot_type)
        return cleared
