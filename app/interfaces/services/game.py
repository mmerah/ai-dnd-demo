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
    def get_game(self, game_id: str) -> GameState:
        pass

    @abstractmethod
    def list_saved_games(self) -> list[GameState]:
        pass

    @abstractmethod
    def remove_game(self, game_id: str) -> None:
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

    @abstractmethod
    def generate_combat_prompt(self, game_state: GameState) -> str:
        """Generate a prompt for the combat agent based on current turn."""
        pass

    @abstractmethod
    def should_auto_continue(self, game_state: GameState) -> bool:
        """Check if combat should auto-continue for NPC/Monster turns."""
        pass

    @abstractmethod
    def get_combat_status(self, game_state: GameState) -> str:
        """Get a brief combat status summary."""
        pass

    @abstractmethod
    def should_auto_end_combat(self, game_state: GameState) -> bool:
        """Check if combat should automatically end (no enemies remaining)."""
        pass

    @abstractmethod
    def reset_combat_tracking(self) -> None:
        """Reset internal combat tracking state when combat ends."""
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


class IPreSaveSanitizer(ABC):
    """Interface for sanitizing game state prior to persistence."""

    @abstractmethod
    def sanitize(self, game_state: GameState) -> None:
        """Mutate game_state to ensure it is in a clean, consistent shape before saving."""
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
    ) -> Message:
        """Add a message to the conversation, auto-extract metadata from game state, and save.

        Metadata (location, NPCs mentioned, combat round) is extracted from the game state.
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
        agent_type: AgentType,
        location: str,
        npcs_mentioned: list[str],
        combat_round: int,
        combat_occurrence: int | None = None,
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
            combat_occurrence: Which combat occurrence this message belongs to

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


class ILocationService(ABC):
    """Location-specific operations and initialization logic."""

    @abstractmethod
    def change_location(
        self,
        game_state: GameState,
        location_id: str,
        location_name: str | None,
        description: str | None,
    ) -> None:
        """Change current location and initialize scenario state if defined."""
        pass

    @abstractmethod
    def initialize_location_from_scenario(
        self,
        game_state: GameState,
        scenario_location: ScenarioLocation,
    ) -> None:
        """First-visit initialization from ScenarioLocation definition."""
        pass
