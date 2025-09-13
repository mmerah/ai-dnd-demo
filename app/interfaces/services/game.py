from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.combat import CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameEventType, GameState, Message, MessageRole
from app.models.instances.monster_instance import MonsterInstance
from app.models.location import EncounterParticipantSpawn
from app.models.monster import MonsterSheet
from app.models.scenario import ScenarioLocation


class IGameFactory(ABC):
    """Interface for creating new game instances."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
        content_packs: list[str] | None = None,
    ) -> GameState:
        """Initialize a new game state.

        Args:
            character: The player's character sheet
            scenario_id: Scenario to load
            content_packs: Additional content packs to use (merged with scenario packs)

        Returns:
            Initialized GameState object
        """
        pass


class IGameService(ABC):
    """Interface for managing game state."""

    @abstractmethod
    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
        content_packs: list[str] | None = None,
    ) -> GameState:
        """Initialize a new game state.

        Creates a new game with the provided character and scenario,
        stores it in memory, and saves it to disk.

        Args:
            character: The player's character sheet
            scenario_id: Scenario to load
            content_packs: Additional content packs to use (merged with scenario packs)

        Returns:
            Initialized GameState object
        """
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
        """Load game state from disk.

        Args:
            game_id: ID of the game to load

        Returns:
            Loaded GameState object

        Raises:
            FileNotFoundError: If save file doesn't exist
            ValueError: If save file is corrupted
        """
        pass

    @abstractmethod
    def get_game(self, game_id: str) -> GameState:
        """Get active game state from memory or load from disk.

        First checks in-memory cache, then attempts to load from disk
        if not found.

        Args:
            game_id: ID of the game

        Returns:
            GameState object

        Raises:
            FileNotFoundError: If game doesn't exist
        """
        pass

    @abstractmethod
    def enrich_for_display(self, game_state: GameState) -> GameState:
        """Enrich game state with display names for frontend presentation.

        Populates item names from definitions for inventory items that
        only have indexes. This is used when sending game state to frontend.

        Args:
            game_state: The game state to enrich

        Returns:
            The enriched game state (modified in place)
        """
        pass

    @abstractmethod
    def list_saved_games(self) -> list[GameState]:
        """List all saved games.

        Returns:
            List of GameState objects for all saved games
        """
        pass

    @abstractmethod
    def remove_game(self, game_id: str) -> None:
        """Remove a game from memory and disk.

        Args:
            game_id: ID of the game to remove
        """
        pass

    @abstractmethod
    def initialize_location_from_scenario(
        self,
        game_state: GameState,
        scenario_location: ScenarioLocation,
    ) -> None:
        """Initialize a location from scenario definition.

        Sets up the location state including NPCs, items, and encounters
        based on the scenario definition.

        Args:
            game_state: Game state to update (modified in-place)
            scenario_location: Location definition from scenario
        """
        pass

    @abstractmethod
    def create_monster_instance(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        """Create a MonsterInstance from a MonsterSheet template.

        Args:
            sheet: Monster template with base stats
            current_location_id: ID of the location where monster spawns

        Returns:
            New MonsterInstance with initialized entity state
        """
        pass

    @abstractmethod
    def recompute_character_state(self, game_state: GameState) -> None:
        """Recompute derived values for the player character.

        Updates computed values like AC, initiative, saves, skills based on
        current character sheet and state. Preserves current HP and resources.

        Args:
            game_state: Game state containing character to update (modified in-place)
        """
        pass


class ICombatService(ABC):
    """Interface for combat-related computations and operations (SOLID/DRY)."""

    @abstractmethod
    def roll_initiative(self, entity: IEntity) -> int:
        """Roll initiative for an entity.

        Formula: d20 + entity's initiative modifier

        Args:
            entity: Entity to roll initiative for

        Returns:
            Initiative roll result
        """
        pass

    @abstractmethod
    def add_participant(self, combat: CombatState, entity: IEntity) -> CombatParticipant:
        """Add an entity to combat.

        Automatically rolls initiative and infers participant type
        (PLAYER, ALLY, or ENEMY) from entity properties.

        Args:
            combat: Combat state to update
            entity: Entity to add to combat

        Returns:
            Created CombatParticipant record
        """
        pass

    @abstractmethod
    def add_participants(self, combat: CombatState, entities: list[IEntity]) -> list[CombatParticipant]:
        """Add multiple entities to combat.

        Args:
            combat: Combat state to update
            entities: List of entities to add

        Returns:
            List of created CombatParticipant records
        """
        pass

    @abstractmethod
    def realize_spawns(
        self,
        game_state: GameState,
        spawns: list[EncounterParticipantSpawn],
        scenario_service: IScenarioService,
        game_service: IGameService,
        repository_provider: IRepositoryProvider,
    ) -> list[IEntity]:
        """Convert encounter spawns into concrete entities.

        Processes spawn definitions with probabilities to create actual
        NPCs or monsters from repositories.

        Args:
            game_state: Current game state
            spawns: List of spawn definitions with probabilities
            scenario_service: Service for accessing scenario NPCs
            monster_repository: Repository for accessing monster templates
            game_service: Service for creating instances

        Returns:
            List of created entity instances
        """
        pass

    @abstractmethod
    def generate_combat_prompt(self, game_state: GameState) -> str:
        """Generate a prompt for the combat agent based on current turn.

        Creates contextual prompt including current combatant, available
        actions, and tactical situation.

        Args:
            game_state: Current game state with combat info

        Returns:
            Formatted prompt string for AI agent
        """
        pass

    @abstractmethod
    def should_auto_continue(self, game_state: GameState) -> bool:
        """Check if combat should auto-continue for NPC/Monster turns.

        Returns True if current turn is an NPC or monster, indicating
        the AI should handle the turn automatically.

        Args:
            game_state: Current game state

        Returns:
            True if combat should continue automatically
        """
        pass

    @abstractmethod
    def should_auto_end_combat(self, game_state: GameState) -> bool:
        """Check if combat should automatically end.

        Returns True when no enemies remain in combat.

        Args:
            game_state: Current game state

        Returns:
            True if combat should end
        """
        pass

    @abstractmethod
    def reset_combat_tracking(self) -> None:
        """Reset internal combat tracking state.

        Called when combat ends to clear any cached state.
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


class ISaveManager(ABC):
    """Interface for managing game save operations."""

    @abstractmethod
    def save_game(self, game_state: GameState) -> Path:
        """Save complete game state to modular structure.

        Creates the following structure:
        saves/[scenario-id]/[game-id]/
            ├── metadata.json
            ├── instances/
            │   ├── character.json
            │   ├── scenario.json
            │   ├── npcs/
            │   │    └── [npc-instance-id].json
            |   └── monsters/
            │       └── [monster-instance-id].json
            ├── conversation_history.json
            └── game_events.json

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
        """Sanitize game state before saving.

        Ensures consistent state by:
        - Removing dead entities from locations
        - Cleaning up invalid references
        - Normalizing data structures

        Args:
            game_state: Game state to sanitize (modified in-place)
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
        """Create a MonsterInstance from a MonsterSheet template.

        Initializes entity state with computed values based on monster stats.

        Args:
            sheet: Monster template with base stats
            current_location_id: ID of spawn location

        Returns:
            MonsterInstance with initialized EntityState
        """
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
        """Change current location.

        Updates location state and initializes scenario-specific content
        if this is the first visit to a scenario location.

        Args:
            game_state: Game state to update (modified in-place)
            location_id: New location ID
            location_name: Optional display name for location
            description: Optional location description
        """
        pass

    @abstractmethod
    def initialize_location_from_scenario(
        self,
        game_state: GameState,
        scenario_location: ScenarioLocation,
    ) -> None:
        """Initialize location on first visit from scenario definition.

        Populates location with NPCs, items, and prepares encounters
        based on scenario configuration.

        Args:
            game_state: Game state to update (modified in-place)
            scenario_location: Location definition from scenario
        """
        pass
