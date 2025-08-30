"""Abstract base class for all specialized agents."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeAlias

from pydantic import BaseModel

from app.interfaces.services import IGameService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState

# Type alias for PydanticAI tool functions
# These are async functions that take a RunContext and return a BaseModel
# The exact parameters vary by tool, so we use a protocol or keep it generic
ToolFunction: TypeAlias = Callable[..., Awaitable[BaseModel]]


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    @abstractmethod
    def get_required_tools(self) -> list[ToolFunction]:
        """Return list of tools this agent requires."""

    @abstractmethod
    def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
