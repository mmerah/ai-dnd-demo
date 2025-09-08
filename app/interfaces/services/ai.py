from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from app.common.types import JSONSerializable
from app.models.ai_response import AIResponse
from app.models.game_state import GameState
from app.models.scenario import ScenarioSheet
from app.models.tool_results import ToolResult


class IAIService(ABC):
    """Interface for the main AI service."""

    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        pass


class IMessageService(ABC):
    """Interface for managing and broadcasting all game messages."""

    @abstractmethod
    async def send_narrative(
        self,
        game_id: str,
        content: str,
        is_chunk: bool = False,
        is_complete: bool = False,
    ) -> None:
        pass

    @abstractmethod
    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, JSONSerializable]) -> None:
        pass

    @abstractmethod
    async def send_tool_result(self, game_id: str, tool_name: str, result: ToolResult) -> None:
        pass

    @abstractmethod
    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        pass

    @abstractmethod
    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        pass

    @abstractmethod
    async def send_complete(self, game_id: str) -> None:
        pass

    @abstractmethod
    def generate_sse_events(
        self,
        game_id: str,
        game_state: GameState,
        scenario: ScenarioSheet | None = None,
        available_scenarios: list[ScenarioSheet] | None = None,
    ) -> AsyncGenerator[dict[str, str], None]:
        pass


class IContextService(ABC):
    """Interface for creating augmented context for AI prompting."""

    @abstractmethod
    def build_context(self, game_state: GameState) -> str:
        pass


class IEventLoggerService(ABC):
    """Interface for logging agentic events."""

    @abstractmethod
    def set_game_id(self, game_id: str) -> None:
        pass

    @abstractmethod
    def log_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def log_tool_result(self, tool_name: str, result: str) -> None:
        pass

    @abstractmethod
    def log_thinking(self, content: str) -> None:
        pass

    @abstractmethod
    def log_error(self, error: Exception) -> None:
        pass
