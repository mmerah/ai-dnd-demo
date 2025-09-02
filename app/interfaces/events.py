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
        pass

    @abstractmethod
    async def submit_commands(self, commands: list[BaseCommand]) -> None:
        pass

    @abstractmethod
    async def execute_command(self, command: BaseCommand) -> BaseModel | None:
        pass

    @abstractmethod
    async def wait_for_completion(self) -> None:
        pass

    @abstractmethod
    async def submit_and_wait(self, commands: list[BaseCommand]) -> None:
        """Submit multiple commands then wait for completion."""
        pass
