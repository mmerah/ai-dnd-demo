"""Time-related command definitions."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class ShortRestCommand(BaseCommand):
    """Command for short rest."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "time"


@dataclass
class LongRestCommand(BaseCommand):
    """Command for long rest."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "time"


@dataclass
class AdvanceTimeCommand(BaseCommand):
    """Command to advance game time."""

    agent_type: AgentType | None = field(default=None)
    minutes: int = 0

    def get_handler_name(self) -> str:
        return "time"
