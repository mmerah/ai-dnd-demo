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
class AddItemCommand(BaseCommand):
    """Command to add item to inventory."""

    item_name: str = ""
    quantity: int = 1

    def get_handler_name(self) -> str:
        return "inventory"


@dataclass
class RemoveItemCommand(BaseCommand):
    """Command to remove item from inventory."""

    item_name: str = ""
    quantity: int = 1

    def get_handler_name(self) -> str:
        return "inventory"
