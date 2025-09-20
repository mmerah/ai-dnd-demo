"""Broadcast-related command definitions."""

from dataclasses import dataclass, field

from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.models.tool_results import ToolResult


@dataclass
class BroadcastNarrativeCommand(BaseCommand):
    """Command to broadcast narrative to frontend."""

    content: str = ""
    is_chunk: bool = False
    is_complete: bool = False

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastToolCallCommand(BaseCommand):
    """Command to broadcast tool call to frontend."""

    tool_name: str = ""
    parameters: dict[str, JSONSerializable] = field(default_factory=dict)

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastToolResultCommand(BaseCommand):
    """Command to broadcast tool result to frontend."""

    tool_name: str = ""
    result: ToolResult | None = None

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastNPCDialogueCommand(BaseCommand):
    """Command to broadcast NPC dialogue to the frontend."""

    npc_id: str = ""
    npc_name: str = ""
    content: str = ""
    complete: bool = True

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastGameUpdateCommand(BaseCommand):
    """Command to broadcast game state update."""

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastPolicyWarningCommand(BaseCommand):
    """Command to broadcast explicit policy warnings to the frontend."""

    message: str = ""
    tool_name: str | None = None
    agent_type: str | None = None

    def get_handler_name(self) -> str:
        return "broadcast"
