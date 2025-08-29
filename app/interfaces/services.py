"""Service interfaces for dependency inversion."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator

from app.models.ai_response import AIResponse
from app.models.character import CharacterSheet
from app.models.game_state import GameState, JSONSerializable, MessageRole
from app.models.scenario import Scenario


class IGameService(ABC):
    """Interface for managing game state."""

    @abstractmethod
    def initialize_game(
        self, character: CharacterSheet, premise: str | None = None, scenario_id: str | None = None
    ) -> GameState:
        pass

    @abstractmethod
    def save_game(self, game_state: GameState) -> str:
        pass

    @abstractmethod
    def load_game(self, game_id: str) -> GameState:
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState | None:
        pass

    @abstractmethod
    def add_message(
        self,
        game_id: str,
        role: MessageRole,
        content: str,
        agent_type: str = "narrative",
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> GameState:
        pass

    @abstractmethod
    def add_game_event(
        self,
        game_id: str,
        event_type: str,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: JSONSerializable | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        pass


class IAIService(ABC):
    """Interface for the main AI service."""

    @abstractmethod
    def generate_response(
        self, user_message: str, game_state: GameState, game_service: IGameService, stream: bool = True
    ) -> AsyncIterator[AIResponse]:
        pass


class IScenarioService(ABC):
    """Interface for managing scenarios."""

    @abstractmethod
    def get_scenario(self, scenario_id: str) -> Scenario | None:
        pass

    @abstractmethod
    def list_scenarios(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def get_scenario_context_for_ai(self, scenario: Scenario, current_location_id: str) -> str:
        pass


class IBroadcastService(ABC):
    """Interface for the pub/sub SSE event streaming service."""

    @abstractmethod
    async def publish(self, game_id: str, event: str, data: JSONSerializable) -> None:
        pass

    @abstractmethod
    async def subscribe(self, game_id: str) -> AsyncGenerator[dict[str, JSONSerializable], None]:
        pass
