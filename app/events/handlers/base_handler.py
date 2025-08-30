"""Base handler class for command processing."""

from abc import ABC, abstractmethod

from app.events.base import BaseCommand, CommandResult
from app.interfaces.services import IGameService
from app.models.game_state import GameState


class BaseHandler(ABC):
    """Base class for all command handlers."""

    def __init__(self, game_service: IGameService):
        self.game_service = game_service

    @abstractmethod
    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle a command and return result with any follow-up commands."""

    @abstractmethod
    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
