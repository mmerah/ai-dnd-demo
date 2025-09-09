from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.interfaces.services.data import IMonsterRepository
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.combat import CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameEventType, GameState, Message, MessageRole
from app.models.instances.monster_instance import MonsterInstance
from app.models.location import EncounterParticipantSpawn
from app.models.monster import MonsterSheet
from app.models.scenario import ScenarioLocation


class IGameService(ABC):
    """Interface for managing game state."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
    ) -> GameState:
        pass

    @abstractmethod
    def save_game(self, game_state: GameState) -> str:
        """Save the game state and return the save path as a string.

        Returns str (stringified Path) for consistency with other API methods
        that return strings for paths, while ISaveManager returns Path objects
        for internal use. This allows the service layer to remain decoupled
        from specific path implementations.
        """
        pass

    @abstractmethod
    def load_game(self, game_id: str) -> GameState:
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState | None:
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

    @abstractmethod
    def create_monster_instance(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        """Create a MonsterInstance from a MonsterSheet template."""
        pass

    @abstractmethod
    def recompute_character_state(self, game_state: GameState) -> None:
        """Recompute derived values for the player character from sheet + state."""
        pass


class ICombatService(ABC):
    """Interface for combat-related computations and operations (SOLID/DRY)."""

    @abstractmethod
    def roll_initiative(self, entity: IEntity) -> int:
        """Roll initiative: d20 + entity's initiative modifier from state."""
        pass

    @abstractmethod
    def add_participant(self, combat: CombatState, entity: IEntity) -> CombatParticipant:
        """Add an entity to combat, rolling initiative and inferring type."""
        pass

    @abstractmethod
    def add_participants(self, combat: CombatState, entities: list[IEntity]) -> list[CombatParticipant]:
        """Add multiple entities to combat, returning their participant records."""
        pass

    @abstractmethod
    def realize_spawns(
        self,
        game_state: GameState,
        spawns: list[EncounterParticipantSpawn],
        scenario_service: IScenarioService,
        monster_repository: IMonsterRepository,
        game_service: IGameService,
    ) -> list[IEntity]:
        """Convert encounter spawns into concrete entities based on probabilities and data sources."""
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


class IConversationService(ABC):
    """Interface for recording narrative messages with metadata and persistence."""

    @abstractmethod
    def record_message(
        self,
        game_state: GameState,
        role: MessageRole,
        content: str,
        agent_type: AgentType = AgentType.NARRATIVE,
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> Message:
        """Add a message to the conversation, auto-extract missing metadata, and save.

        Returns the created Message.
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
        agent_type: AgentType = AgentType.NARRATIVE,
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


class IEventManager(ABC):
    """Interface for managing game events."""

    @abstractmethod
    def add_event(
        self,
        game_state: GameState,
        event_type: GameEventType,
        tool_name: str,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game event.

        Args:
            game_state: Game state to update
            event_type: Type of event (GameEventType enum)
            tool_name: Tool that generated the event
            parameters: Event parameters
            result: Event result
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
    def get_current_location(self, game_state: GameState) -> str | None:
        """Get the current location

        Args:
            game_state: Current game state

        Returns:
            Current location or None if not available
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


class IMonsterFactory(ABC):
    """Factory for creating MonsterInstance objects from templates."""

    @abstractmethod
    def create(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        """Map MonsterSheet → MonsterInstance with a proper EntityState."""
        pass
