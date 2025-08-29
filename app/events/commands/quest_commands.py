"""Commands for quest management."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class StartQuestCommand(BaseCommand):
    """Command to start a new quest."""

    quest_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class CompleteObjectiveCommand(BaseCommand):
    """Command to complete a quest objective."""

    quest_id: str = ""
    objective_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class CompleteQuestCommand(BaseCommand):
    """Command to complete an entire quest."""

    quest_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class ProgressActCommand(BaseCommand):
    """Command to progress to the next act."""

    def get_handler_name(self) -> str:
        return "quest"
