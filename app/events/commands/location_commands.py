"""Commands for location and navigation management."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class ChangeLocationCommand(BaseCommand):
    """Command to change the current location."""

    agent_type: AgentType | None = field(default=None)
    location_id: str = ""
    location_name: str | None = None
    description: str | None = None

    def get_handler_name(self) -> str:
        return "location"


@dataclass
class DiscoverSecretCommand(BaseCommand):
    """Command to discover a secret in current location."""

    agent_type: AgentType | None = field(default=None)
    secret_id: str = ""
    secret_description: str = ""

    def get_handler_name(self) -> str:
        return "location"


@dataclass
class UpdateLocationStateCommand(BaseCommand):
    """Command to update location state."""

    agent_type: AgentType | None = field(default=None)
    location_id: str = ""
    danger_level: str | None = None
    complete_encounter: str | None = None
    add_effect: str | None = None

    def get_handler_name(self) -> str:
        return "location"


@dataclass
class MoveNPCCommand(BaseCommand):
    """Move an NPC instance to a specific scenario location by ID."""

    agent_type: AgentType | None = field(default=None)
    npc_id: str = ""
    to_location_id: str = ""

    def get_handler_name(self) -> str:
        return "location"
