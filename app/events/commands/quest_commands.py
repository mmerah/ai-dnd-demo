"""Commands for quest management."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class StartQuestCommand(BaseCommand):
    """Command to start a new quest."""

    agent_type: AgentType | None = field(default=None)
    quest_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class CompleteObjectiveCommand(BaseCommand):
    """Command to complete a quest objective."""

    agent_type: AgentType | None = field(default=None)
    quest_id: str = ""
    objective_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class CompleteQuestCommand(BaseCommand):
    """Command to complete an entire quest."""

    agent_type: AgentType | None = field(default=None)
    quest_id: str = ""

    def get_handler_name(self) -> str:
        return "quest"


@dataclass
class ProgressActCommand(BaseCommand):
    """Command to progress to the next act."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "quest"
