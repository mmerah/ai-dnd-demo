"""Inventory-related command definitions."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class ModifyCurrencyCommand(BaseCommand):
    """Command to modify character currency."""

    agent_type: AgentType | None = field(default=None)
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def get_handler_name(self) -> str:
        return "inventory"


@dataclass
class ModifyInventoryCommand(BaseCommand):
    """Command to modify an inventory item quantity (positive=add, negative=remove)."""

    agent_type: AgentType | None = field(default=None)
    item_index: str = ""
    quantity: int = 0

    def get_handler_name(self) -> str:
        return "inventory"


@dataclass
class EquipItemCommand(BaseCommand):
    """Command to equip or unequip an item."""

    agent_type: AgentType | None = field(default=None)
    item_index: str = ""
    equipped: bool = True

    def get_handler_name(self) -> str:
        return "inventory"
