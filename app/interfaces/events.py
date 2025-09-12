"""Event and command interfaces for dependency inversion."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.events.base import BaseCommand

T = TypeVar("T")


class IEventBus(ABC):
    """Interface for the central command and event bus."""

    @abstractmethod
    async def submit_command(self, command: BaseCommand) -> None:
        """Submit a command for asynchronous execution.

        Args:
            command: Command to execute
        """
        pass

    @abstractmethod
    async def submit_commands(self, commands: list[BaseCommand]) -> None:
        """Submit multiple commands for asynchronous execution.

        Args:
            commands: List of commands to execute
        """
        pass

    @abstractmethod
    async def execute_command(self, command: BaseCommand) -> BaseModel | None:
        """Execute a command synchronously and return its result.

        Args:
            command: Command to execute

        Returns:
            Command result or None if no result
        """
        pass

    @abstractmethod
    async def wait_for_completion(self) -> None:
        """Wait for all pending commands to complete."""
        pass

    @abstractmethod
    async def submit_and_wait(self, commands: list[BaseCommand]) -> None:
        """Submit multiple commands and wait for all to complete.

        Convenience method that combines submit_commands and wait_for_completion.

        Args:
            commands: List of commands to execute
        """
        pass
