"""Base handler class for command processing."""

from abc import ABC, abstractmethod

from app.events.base import BaseCommand, CommandResult
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState


class BaseHandler(ABC):
    """Base class for all command handlers."""

    supported_commands: tuple[type[BaseCommand], ...] = ()

    def __init__(self, game_service: IGameService):
        self.game_service = game_service

    @abstractmethod
    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle a command and return result with any follow-up commands."""

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        if not self.supported_commands:
            raise NotImplementedError(f"Handler {self.__class__.__name__} must define 'supported_commands'")
        return isinstance(command, self.supported_commands)
