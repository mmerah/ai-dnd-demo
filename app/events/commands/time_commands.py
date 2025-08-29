"""Time-related command definitions."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class ShortRestCommand(BaseCommand):
    """Command for short rest."""

    def get_handler_name(self) -> str:
        return "time"


@dataclass
class LongRestCommand(BaseCommand):
    """Command for long rest."""

    def get_handler_name(self) -> str:
        return "time"


@dataclass
class AdvanceTimeCommand(BaseCommand):
    """Command to advance game time."""

    minutes: int = 0

    def get_handler_name(self) -> str:
        return "time"
