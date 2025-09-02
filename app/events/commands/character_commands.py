"""Character-related command definitions."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class UpdateHPCommand(BaseCommand):
    """Command to update character or NPC hit points."""

    target: str = "player"  # 'player' or NPC name
    amount: int = 0  # negative for damage, positive for healing
    damage_type: str = "untyped"

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class UpdateConditionCommand(BaseCommand):
    """Command to add or remove a condition from a target."""

    target: str = "player"  # 'player' or NPC name
    condition: str = ""
    action: str = "add"  # 'add' or 'remove'
    duration: int = 0

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class UpdateSpellSlotsCommand(BaseCommand):
    """Command to update spell slots."""

    level: int = 1
    amount: int = 0

    def get_handler_name(self) -> str:
        return "character"
