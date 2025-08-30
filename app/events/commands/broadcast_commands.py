"""Broadcast-related command definitions."""

from dataclasses import dataclass, field

from app.common.types import JSONSerializable
from app.events.base import BaseCommand


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
    result: JSONSerializable | None = None

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastGameUpdateCommand(BaseCommand):
    """Command to broadcast game state update."""

    def get_handler_name(self) -> str:
        return "broadcast"


@dataclass
class BroadcastCharacterUpdateCommand(BaseCommand):
    """Command to broadcast character update."""

    def get_handler_name(self) -> str:
        return "broadcast"
