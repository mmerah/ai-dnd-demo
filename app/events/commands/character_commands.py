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
class AddConditionCommand(BaseCommand):
    """Command to add a status condition."""

    target: str = "player"
    condition: str = ""
    duration: int = 0

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class RemoveConditionCommand(BaseCommand):
    """Command to remove a status condition."""

    target: str = "player"
    condition: str = ""

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class UpdateSpellSlotsCommand(BaseCommand):
    """Command to update spell slots."""

    level: int = 1
    amount: int = 0

    def get_handler_name(self) -> str:
        return "character"
