"""Item models for D&D 5e inventory system."""

from enum import Enum

from pydantic import BaseModel, Field


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

    # Weapon properties
    damage: str | None = None  # e.g., "1d8"
    damage_type: str | None = None  # e.g., "Piercing"
    properties: list[str] = Field(default_factory=list)  # e.g., ["Finesse", "Light"]

    # Armor properties
    armor_class: int | None = None
    dex_bonus: bool | None = None

    # Equipment pack contents
    contents: list[str] = Field(default_factory=list)

    # Shop/availability
    quantity_available: int | None = None  # For shops


class InventoryItem(BaseModel):
    """Item instance in a character's inventory."""

    name: str
    quantity: int = Field(ge=1, default=1)
    equipped_quantity: int = Field(ge=0, default=0)

    # These can be populated from ItemDefinition when needed
    weight: float = Field(ge=0, default=0.0)
    value: float = Field(ge=0, default=0)  # Value in gold pieces
    description: str = ""
    item_type: ItemType | None = None

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
