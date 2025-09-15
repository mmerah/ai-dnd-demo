"""Item models for D&D 5e inventory system."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.equipment_slots import EquipmentSlotType


class ItemType(str, Enum):
    """Types of items in the game."""

    WEAPON = "Weapon"
    ARMOR = "Armor"
    POTION = "Potion"
    AMMUNITION = "Ammunition"
    ADVENTURING_GEAR = "Adventuring Gear"
    EQUIPMENT_PACK = "Equipment Pack"


class ItemRarity(str, Enum):
    """Item rarity levels."""

    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    VERY_RARE = "Very Rare"
    LEGENDARY = "Legendary"
    ARTIFACT = "Artifact"
    VARIES = "Varies"


class ItemSubtype(str, Enum):
    """Subtypes for weapons and armor."""

    # Weapon subtypes
    MELEE = "Melee"
    RANGED = "Ranged"
    # Armor subtypes
    LIGHT = "Light"
    MEDIUM = "Medium"
    HEAVY = "Heavy"
    SHIELD = "Shield"


class ItemDefinition(BaseModel):
    """Definition of an item type from data files."""

    index: str
    name: str
    type: ItemType
    rarity: ItemRarity
    weight: float = Field(ge=0, default=0.0)
    value: float = Field(ge=0, default=0)
    description: str

    # Optional fields for different item types
    subtype: ItemSubtype | None = None

    # Weapon properties. Empty if not weapon
    damage: str = ""
    damage_type: str = ""
    properties: list[str] = Field(default_factory=list)

    # Armor properties. 0/False if not armore
    armor_class: int = 0
    dex_bonus: bool = False

    # Equipment pack contents
    contents: list[str] = Field(default_factory=list)

    # Shop/availability. -1 for unlimited
    quantity_available: int = -1

    # Content pack this item comes from
    content_pack: str

    # Valid equipment slots for this item
    valid_slots: list[EquipmentSlotType] = Field(default_factory=list)

    @property
    def is_two_handed(self) -> bool:
        """Determine if weapon requires both hands."""
        return "Two-Handed" in (self.properties or []) or "two-handed" in self.name.lower()

    def get_valid_slots(self) -> list[EquipmentSlotType]:
        """Get valid equipment slots with fail-fast validation."""
        if self.valid_slots:
            return self.valid_slots

        if self.type == ItemType.ARMOR:
            if self.subtype == ItemSubtype.SHIELD:
                return [EquipmentSlotType.OFF_HAND, EquipmentSlotType.MAIN_HAND]
            elif (
                self.subtype == ItemSubtype.LIGHT
                or self.subtype == ItemSubtype.MEDIUM
                or self.subtype == ItemSubtype.HEAVY
            ):
                return [EquipmentSlotType.CHEST]
            else:
                raise ValueError(f"Unknown armor subtype: {self.subtype}")
        elif self.type == ItemType.WEAPON:
            if self.is_two_handed:
                return [EquipmentSlotType.MAIN_HAND]
            else:
                return [EquipmentSlotType.MAIN_HAND, EquipmentSlotType.OFF_HAND]
        elif self.type == ItemType.AMMUNITION:
            return [EquipmentSlotType.AMMUNITION]
        elif self.type == ItemType.ADVENTURING_GEAR:
            # Special handling for rings and amulets
            if self.index.startswith("ring-"):
                return [EquipmentSlotType.RING_1, EquipmentSlotType.RING_2]
            elif self.index.startswith("amulet-"):
                return [EquipmentSlotType.NECK]

        # Non-equippable items return empty list
        return []

    def is_equippable(self) -> bool:
        """Check if item can be equipped."""
        return len(self.get_valid_slots()) > 0

    # --- Normalization validators for legacy/loose item inputs ---
    @field_validator("description", mode="before")
    @classmethod
    def _normalize_description(cls, v: str | None) -> str:
        return v or ""

    @field_validator("damage", mode="before")
    @classmethod
    def _normalize_damage(cls, v: str | None) -> str:
        return v or ""

    @field_validator("damage_type", mode="before")
    @classmethod
    def _normalize_damage_type(cls, v: str | None) -> str:
        return v or ""

    @field_validator("properties", mode="before")
    @classmethod
    def _normalize_properties(cls, v: Any) -> list[str]:
        return v or []

    @field_validator("armor_class", mode="before")
    @classmethod
    def _normalize_armor_class(cls, v: Any) -> int:
        if v is None:
            return 0
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, int | float):
            return int(v)
        try:
            return int(str(v))
        except Exception:
            return 0

    @field_validator("dex_bonus", mode="before")
    @classmethod
    def _normalize_dex_bonus(cls, v: Any) -> bool:
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, int | float):
            return v != 0
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("true", "yes", "y", "1"):
                return True
            if val in ("false", "no", "n", "0", ""):
                return False
        return False

    @field_validator("contents", mode="before")
    @classmethod
    def _normalize_contents(cls, v: Any) -> list[str]:
        return v or []

    @field_validator("weight", mode="before")
    @classmethod
    def _normalize_weight(cls, v: Any) -> float:
        if v is None:
            return 0.0
        if isinstance(v, int | float):
            return float(v)
        try:
            return float(str(v))
        except Exception:
            return 0.0

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_value(cls, v: Any) -> float:
        if v is None:
            return 0.0
        if isinstance(v, int | float):
            return float(v)
        try:
            return float(str(v))
        except Exception:
            return 0.0

    @field_validator("quantity_available", mode="before")
    @classmethod
    def _normalize_quantity_available(cls, v: Any) -> int:
        if v is None:
            return -1
        if isinstance(v, int | float):
            return int(v)
        try:
            return int(str(v))
        except Exception:
            return -1


class InventoryItem(BaseModel):
    """Item instance in inventory."""

    index: str
    name: str | None = None
    item_type: ItemType | None = None
    quantity: int = Field(ge=1, default=1)

    @classmethod
    def from_definition(cls, definition: ItemDefinition, quantity: int = 1) -> "InventoryItem":
        """Create an inventory item from an item definition."""
        return cls(
            index=definition.index,
            name=definition.name,
            item_type=definition.type,
            quantity=quantity,
        )
