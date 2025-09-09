"""Item models for D&D 5e inventory system."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


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

    name: str
    type: ItemType
    rarity: ItemRarity
    weight: float = Field(ge=0, default=0.0)
    value: float = Field(ge=0, default=0)  # Value in gold pieces
    description: str

    # Optional fields for different item types
    subtype: ItemSubtype | None = None

    # Weapon properties. Empty if not weapon
    damage: str = ""
    damage_type: str = ""
    properties: list[str] = Field(default_factory=list)  # e.g., ["Finesse", "Light"]

    # Armor properties. 0/False if not armore
    armor_class: int = 0
    dex_bonus: bool = False

    # Equipment pack contents
    contents: list[str] = Field(default_factory=list)

    # Shop/availability. -1 for unlimited
    quantity_available: int = -1

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
    """Item instance in a character's inventory."""

    name: str
    quantity: int = Field(ge=1, default=1)
    equipped_quantity: int = Field(ge=0, default=0)

    # These can be populated from ItemDefinition when needed
    weight: float = Field(ge=0, default=0.0)
    value: float = Field(ge=0, default=0)
    description: str = ""
    item_type: ItemType = ItemType.ADVENTURING_GEAR

    @classmethod
    def from_definition(
        cls, definition: ItemDefinition, quantity: int = 1, equipped_quantity: int = 0
    ) -> "InventoryItem":
        """Create an inventory item from an item definition."""
        return cls(
            name=definition.name,
            quantity=quantity,
            equipped_quantity=equipped_quantity,
            weight=definition.weight,
            value=definition.value,
            description=definition.description,
            item_type=definition.type,
        )

    def model_post_init(self, __context: object) -> None:
        # Ensure equipped_quantity does not exceed quantity
        if self.equipped_quantity < 0:
            self.equipped_quantity = 0
        if self.equipped_quantity > self.quantity:
            self.equipped_quantity = self.quantity

    def get_total_weight(self) -> float:
        """Calculate total weight for stacked items."""
        return self.weight * self.quantity

    def get_total_value(self) -> float:
        """Calculate total value for stacked items."""
        return self.value * self.quantity
