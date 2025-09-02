"""Inventory-related command definitions."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class ModifyCurrencyCommand(BaseCommand):
    """Command to modify character currency."""

    gold: int = 0
    silver: int = 0
    copper: int = 0

    def get_handler_name(self) -> str:
        return "inventory"


@dataclass
class ModifyInventoryCommand(BaseCommand):
    """Command to modify an inventory item quantity (positive=add, negative=remove)."""

    item_name: str = ""
    quantity: int = 0

    def get_handler_name(self) -> str:
        return "inventory"
