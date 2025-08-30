"""Service interfaces for dependency inversion."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator

from pydantic import BaseModel

from app.common.types import JSONSerializable
from app.models.ai_response import AIResponse
from app.models.character import CharacterSheet
from app.models.combat import CombatState
from app.models.game_state import GameState, MessageRole
from app.models.item import ItemDefinition
from app.models.npc import NPCSheet
from app.models.quest import Quest
from app.models.scenario import Scenario
from app.models.spell import SpellDefinition
from app.models.sse_events import ConnectionInfo


class ICharacterService(ABC):
    """Interface for managing character data."""

    @abstractmethod
    def get_character(self, character_id: str) -> CharacterSheet | None:
        pass

    @abstractmethod
    def list_characters(self) -> list[CharacterSheet]:
        pass

    @abstractmethod
    def get_all_characters(self) -> list[CharacterSheet]:
        pass

    @abstractmethod
    def validate_character_references(self, character: CharacterSheet) -> list[str]:
        pass


class IGameService(ABC):
    """Interface for managing game state."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        premise: str | None = None,
        scenario_id: str | None = None,
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
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        pass

    @abstractmethod
    def list_saved_games(self) -> list[GameState]:
        pass


class IAIService(ABC):
    """Interface for the main AI service."""

    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        pass


class IScenarioService(ABC):
    """Interface for managing scenarios."""

    @abstractmethod
    def get_scenario(self, scenario_id: str) -> Scenario | None:
        pass

    @abstractmethod
    def list_scenarios(self) -> list[Scenario]:
        pass

    @abstractmethod
    def get_scenario_context_for_ai(self, scenario: Scenario, current_location_id: str) -> str:
        pass


class IBroadcastService(ABC):
    """Interface for the pub/sub SSE event streaming service.

    The data parameter expects Pydantic BaseModel instances that can be
    serialized to JSON for SSE transmission.
    """

    @abstractmethod
    async def publish(self, game_id: str, event: str, data: BaseModel) -> None:
        """Publish an SSE event with Pydantic model data."""
        pass

    @abstractmethod
    def subscribe(self, game_id: str) -> AsyncGenerator[dict[str, str], None]:
        """Subscribe to SSE events, yields formatted SSE dictionaries."""
        pass


class IDataService(ABC):
    """Interface for loading and managing game data."""

    @abstractmethod
    def get_item(self, name: str, allow_missing: bool = False) -> ItemDefinition | None:
        pass

    @abstractmethod
    def get_monster(self, name: str, allow_missing: bool = False) -> NPCSheet | None:
        pass

    @abstractmethod
    def get_spell(self, name: str, allow_missing: bool = False) -> SpellDefinition | None:
        pass

    @abstractmethod
    def list_items(self) -> list[str]:
        pass

    @abstractmethod
    def list_monsters(self) -> list[str]:
        pass

    @abstractmethod
    def list_spells(self) -> list[str]:
        pass

    @abstractmethod
    def validate_item_reference(self, name: str) -> bool:
        pass

    @abstractmethod
    def validate_monster_reference(self, name: str) -> bool:
        pass

    @abstractmethod
    def validate_spell_reference(self, name: str) -> bool:
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
    async def send_character_update(self, game_id: str, character: CharacterSheet) -> None:
        pass

    @abstractmethod
    async def send_combat_update(self, game_id: str, combat: CombatState) -> None:
        pass

    @abstractmethod
    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        pass

    # TODO: Ideally just a game_id and location model like others
    @abstractmethod
    async def send_location_update(
        self,
        game_id: str,
        location_id: str,
        location_name: str,
        description: str,
        connections: list[ConnectionInfo],
        danger_level: str,
        npcs_present: list[str],
    ) -> None:
        pass

    # TODO: Can't we just send a list of all quests ?
    @abstractmethod
    async def send_quest_update(
        self,
        game_id: str,
        active_quests: list[Quest],
        completed_quest_ids: list[str],
    ) -> None:
        pass

    @abstractmethod
    async def send_act_update(self, game_id: str, act_id: str, act_name: str, act_index: int) -> None:
        pass
