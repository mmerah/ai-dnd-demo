"""Abstract base class for all specialized agents."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from typing import Any

from app.interfaces.services import IGameService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    @abstractmethod
    def get_required_tools(self) -> list[Callable[..., Any]]:
        """Return list of tools this agent requires."""
        pass

    @abstractmethod
    def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        pass
