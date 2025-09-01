"""Service interfaces for dependency inversion."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from datetime import datetime
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.common.types import JSONSerializable
from app.models.ai_response import AIResponse
from app.models.character import CharacterSheet
from app.models.game_state import GameEvent, GameEventType, GameState, Message, MessageRole
from app.models.item import ItemDefinition, ItemRarity, ItemType
from app.models.npc import NPCSheet
from app.models.scenario import Scenario, ScenarioLocation
from app.models.spell import SpellDefinition, SpellSchool
from app.models.tool_results import ToolResult


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
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        pass

    @abstractmethod
    def list_saved_games(self) -> list[GameState]:
        pass

    @abstractmethod
    def initialize_location_from_scenario(
        self,
        game_state: GameState,
        scenario_location: ScenarioLocation,
    ) -> None:
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
    def get_default_scenario(self) -> Scenario | None:
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
    async def send_character_update(self, game_id: str, character: CharacterSheet) -> None:
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
        scenario: Scenario | None = None,
        available_scenarios: list[Scenario] | None = None,
    ) -> AsyncGenerator[dict[str, str], None]:
        pass


# Type variable for generic interfaces
T = TypeVar("T")


class IPathResolver(ABC):
    """Interface for resolving file paths in the application."""

    @abstractmethod
    def get_data_dir(self) -> Path:
        """Get the root data directory."""
        pass

    @abstractmethod
    def get_saves_dir(self) -> Path:
        """Get the root saves directory."""
        pass

    @abstractmethod
    def get_scenario_dir(self, scenario_id: str) -> Path:
        """Get directory for a specific scenario."""
        pass

    @abstractmethod
    def get_character_file(self, character_id: str) -> Path:
        """Get path to a character file."""
        pass

    @abstractmethod
    def get_save_dir(self, scenario_id: str, game_id: str, create: bool = False) -> Path:
        """Get directory for a saved game.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game
            create: If True, create the directory if it doesn't exist
        """
        pass

    @abstractmethod
    def resolve_scenario_component(self, scenario_id: str, component: str, item_id: str) -> Path:
        """Resolve path to a scenario component file."""
        pass

    @abstractmethod
    def get_shared_data_file(self, data_type: str) -> Path:
        """Get path to a shared data file (items, spells, monsters)."""
        pass


class IRepository(ABC, Generic[T]):
    """Base interface for data repositories."""

    @abstractmethod
    def get(self, key: str) -> T | None:
        """Get an item by its key."""
        pass

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all available keys."""
        pass

    @abstractmethod
    def validate_reference(self, key: str) -> bool:
        """Check if a reference exists."""
        pass


class IItemRepository(IRepository[ItemDefinition]):
    """Repository interface for item data."""

    @abstractmethod
    def get_by_type(self, item_type: ItemType) -> list[ItemDefinition]:
        """Get all items of a specific type."""
        pass

    @abstractmethod
    def get_by_rarity(self, rarity: ItemRarity) -> list[ItemDefinition]:
        """Get all items of a specific rarity."""
        pass


class IMonsterRepository(IRepository[NPCSheet]):
    """Repository interface for monster data."""

    @abstractmethod
    def get_by_challenge_rating(self, min_cr: float, max_cr: float) -> list[NPCSheet]:
        """Get all monsters within a challenge rating range."""
        pass

    @abstractmethod
    def get_by_type(self, creature_type: str) -> list[NPCSheet]:
        """Get all monsters of a specific type."""
        pass


class ISpellRepository(IRepository[SpellDefinition]):
    """Repository interface for spell data."""

    @abstractmethod
    def get_by_level(self, level: int) -> list[SpellDefinition]:
        """Get all spells of a specific level."""
        pass

    @abstractmethod
    def get_by_school(self, school: SpellSchool) -> list[SpellDefinition]:
        """Get all spells of a specific school."""
        pass

    @abstractmethod
    def get_by_class(self, class_name: str) -> list[SpellDefinition]:
        """Get all spells available to a specific class."""
        pass


class ILoader(ABC, Generic[T]):
    """Base interface for data loaders."""

    @abstractmethod
    def load(self, path: Path) -> T:
        """Load data from a file."""
        pass

    @abstractmethod
    def save(self, path: Path, data: T) -> None:
        """Save data to a file."""
        pass


class ISaveManager(ABC):
    """Interface for managing game save operations."""

    @abstractmethod
    def save_game(self, game_state: GameState) -> Path:
        """Save complete game state to modular structure.

        Args:
            game_state: Game state to save

        Returns:
            Path to the save directory
        """
        pass

    @abstractmethod
    def load_game(self, scenario_id: str, game_id: str) -> GameState:
        """Load complete game state from modular structure.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            Loaded game state
        """
        pass

    @abstractmethod
    def list_saved_games(self, scenario_id: str | None = None) -> list[tuple[str, str, datetime]]:
        """List all saved games.

        Args:
            scenario_id: Optional filter by scenario

        Returns:
            List of (scenario_id, game_id, last_saved) tuples
        """
        pass

    @abstractmethod
    def game_exists(self, scenario_id: str, game_id: str) -> bool:
        """Check if a saved game exists.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            True if save exists
        """
        pass


class IGameStateManager(ABC):
    """Interface for managing active game states in memory."""

    @abstractmethod
    def store_game(self, game_state: GameState) -> None:
        """Store a game state in memory.

        Args:
            game_state: Game state to store
        """
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState | None:
        """Get a game state from memory.

        Args:
            game_id: ID of the game

        Returns:
            Game state or None if not found
        """
        pass

    @abstractmethod
    def remove_game(self, game_id: str) -> None:
        """Remove a game state from memory.

        Args:
            game_id: ID of the game to remove
        """
        pass

    @abstractmethod
    def list_active_games(self) -> list[str]:
        """List all active game IDs.

        Returns:
            List of game IDs currently in memory
        """
        pass


class IMessageManager(ABC):
    """Interface for managing conversation history."""

    @abstractmethod
    def add_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: str = "narrative",
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> Message:
        """Add a message to conversation history.

        Args:
            game_state: Game state to update
            role: Message role
            content: Message content
            agent_type: Which agent generated this
            location: Where this occurred
            npcs_mentioned: NPCs referenced
            combat_round: Combat round if in combat

        Returns:
            Created message
        """
        pass

    @abstractmethod
    def get_recent_messages(self, game_state: GameState, limit: int = 10) -> list[Message]:
        """Get recent messages from conversation history.

        Args:
            game_state: Game state to read from
            limit: Maximum number of messages

        Returns:
            List of recent messages
        """
        pass

    @abstractmethod
    def clear_old_messages(self, game_state: GameState, keep_recent: int = 100) -> None:
        """Clear old messages keeping only recent ones.

        Args:
            game_state: Game state to update
            keep_recent: Number of recent messages to keep
        """
        pass


class IEventManager(ABC):
    """Interface for managing game events."""

    @abstractmethod
    def add_event(
        self,
        game_state: GameState,
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game event.

        Args:
            game_state: Game state to update
            event_type: Type of event (GameEventType enum)
            tool_name: Tool that generated the event
            parameters: Event parameters
            result: Event result
            metadata: Additional metadata
        """
        pass

    @abstractmethod
    def get_recent_events(self, game_state: GameState, limit: int = 50) -> list[GameEvent]:
        """Get recent game events.

        Args:
            game_state: Game state to read from
            limit: Maximum number of events

        Returns:
            List of recent events
        """
        pass

    @abstractmethod
    def get_events_by_type(self, game_state: GameState, event_type: GameEventType) -> list[GameEvent]:
        """Get events of a specific type.

        Args:
            game_state: Game state to read from
            event_type: Type of events to retrieve (GameEventType enum)

        Returns:
            List of matching events
        """
        pass


class IMetadataService(ABC):
    """Interface for extracting metadata from messages."""

    @abstractmethod
    def extract_npcs_mentioned(self, content: str, known_npcs: list[str]) -> list[str]:
        """Extract NPC names mentioned in content.

        Args:
            content: Message content to analyze
            known_npcs: List of known NPC names

        Returns:
            List of mentioned NPC names
        """
        pass

    @abstractmethod
    def extract_location(self, content: str, current_location: str | None) -> str | None:
        """Extract location from content.

        Args:
            content: Message content to analyze
            current_location: Current location for context

        Returns:
            Extracted location or None
        """
        pass

    @abstractmethod
    def extract_combat_round(self, content: str, in_combat: bool) -> int | None:
        """Extract combat round from content.

        Args:
            content: Message content to analyze
            in_combat: Whether currently in combat

        Returns:
            Combat round number or None
        """
        pass

    @abstractmethod
    def extract_npc_mentions(self, content: str, npcs: Sequence[NPCSheet | str]) -> list[str]:
        """Extract NPC mentions from content with flexible NPC types.

        Args:
            content: Message content to analyze
            npcs: List of NPCs (either NPCSheet objects or string names)

        Returns:
            List of NPC names found in the content
        """
        pass

    @abstractmethod
    def get_current_location(self, game_state: GameState) -> str:
        """Get the current location from game state.

        Args:
            game_state: Current game state

        Returns:
            Current location name
        """
        pass

    @abstractmethod
    def get_combat_round(self, game_state: GameState) -> int | None:
        """Get the current combat round if in combat.

        Args:
            game_state: Current game state

        Returns:
            Current combat round number or None if not in combat
        """
        pass
