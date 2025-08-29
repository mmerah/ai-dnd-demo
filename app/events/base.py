"""Base classes for event-driven architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class CommandPriority(Enum):
    """Priority levels for command processing."""

    HIGH = 1  # System critical (errors, stops)
    NORMAL = 2  # Game state changes
    LOW = 3  # Broadcasts, logging


@dataclass
class BaseCommand(ABC):
    """Base class for all commands in the system."""

    game_id: str = ""  # Required field first
    command_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: CommandPriority = field(default=CommandPriority.NORMAL)

    @abstractmethod
    def get_handler_name(self) -> str:
        """Return the name of the handler for this command."""
        pass


@dataclass
class BaseEvent(ABC):
    """Base class for events that are broadcast to frontend."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    game_id: str = ""

    @abstractmethod
    def get_event_name(self) -> str:
        """Return the name of the SSE event."""
        pass


class CommandResult:
    """Result of command execution."""

    def __init__(self, success: bool, data: dict[str, Any] | None = None, error: str | None = None):
        self.success = success
        self.data = data if data is not None else {}
        self.error = error
        self.follow_up_commands: list[BaseCommand] = []

    def add_command(self, command: BaseCommand) -> None:
        """Add a follow-up command to be executed."""
        self.follow_up_commands.append(command)
