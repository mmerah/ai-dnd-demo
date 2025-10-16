"""Commands for party management."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class AddPartyMemberCommand(BaseCommand):
    """Command to add an NPC to the party."""

    agent_type: AgentType | None = field(default=None)
    npc_id: str = ""

    def get_handler_name(self) -> str:
        return "party"


@dataclass
class RemovePartyMemberCommand(BaseCommand):
    """Command to remove an NPC from the party."""

    agent_type: AgentType | None = field(default=None)
    npc_id: str = ""

    def get_handler_name(self) -> str:
        return "party"
