"""Base classes for event-driven architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel


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
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: CommandPriority = field(default=CommandPriority.NORMAL)

    @abstractmethod
    def get_handler_name(self) -> str:
        """Return the name of the handler for this command."""


@dataclass
class BaseEvent(ABC):
    """Base class for events that are broadcast to frontend."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    game_id: str = ""

    @abstractmethod
    def get_event_name(self) -> str:
        """Return the name of the SSE event."""


class CommandResult:
    """Result of command execution. Errors are handled via exceptions."""

    def __init__(self, data: BaseModel | None = None):
        self.data = data
        self.follow_up_commands: list[BaseCommand] = []
        # Indicates mutated game state requiring save
        self.mutated: bool = False
        # Indicates that character state needs to be recomputed after this command
        self.recompute_state: bool = False

    def add_command(self, command: BaseCommand) -> None:
        """Add a follow-up command to be executed."""
        self.follow_up_commands.append(command)
