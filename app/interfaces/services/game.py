from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.models.character import CharacterSheet
from app.models.combat import CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameEventType, GameState, Message, MessageRole
from app.models.instances.monster_instance import MonsterInstance
from app.models.location import EncounterParticipantSpawn
from app.models.monster import MonsterSheet
from app.models.scenario import ScenarioLocation


class IGameEnrichmentService(ABC):
    """Display enrichment."""

    @abstractmethod
    def enrich_for_display(self, game_state: GameState) -> GameState:
        """Add display names to items for frontend.

        Populates item names from definitions for inventory items that
        only have indexes. This is used when sending game state to frontend.

        Args:
            game_state: The game state to enrich

        Returns:
            The enriched game state (modified in place)
        """
        pass


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
    def generate_combat_prompt(
        self,
        game_state: GameState,
        last_entity_id: str | None = None,
        last_round: int = 0,
    ) -> str:
        """Generate a prompt for the combat agent based on current turn.

        Creates contextual prompt including current combatant, available
        actions, and tactical situation. Supports duplicate turn detection.

        Args:
            game_state: Current game state with combat info
            last_entity_id: Previously prompted entity ID for duplicate detection
            last_round: Previously prompted round number

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
    def ensure_player_in_combat(self, game_state: GameState) -> CombatParticipant | None:
        """Ensure player is added to combat if not already present.

        Automatically adds the player character to combat if they're not
        already a participant.

        Args:
            game_state: Current game state with active combat

        Returns:
            CombatParticipant if player was added, None if already present

        Raises:
            ValueError: If combat is not active
        """
        pass

    @abstractmethod
    def spawn_free_monster(self, game_state: GameState, monster_index: str) -> IEntity | None:
        """Spawn a free-roaming monster from the repository.

        Creates a monster instance from repository data and adds it to game state.
        Does not add to combat automatically.

        Args:
            game_state: Current game state
            monster_index: ID of monster to spawn

        Returns:
            Created monster entity or None if not found
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
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
    ) -> Message:
        """Add a message to the conversation, auto-extract metadata from game state, and save.

        Metadata (location, NPCs mentioned, combat round) is extracted from the game state.
        Returns the created Message.
        """
        pass

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
        speaker_npc_id: str | None = None,
        speaker_npc_name: str | None = None,
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
            speaker_npc_id: ID of NPC speaker (if applicable)
            speaker_npc_name: Name of NPC speaker (if applicable)

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
    def extract_targeted_npcs(self, message: str, game_state: GameState) -> list[str]:
        """Determine which NPCs are being directly addressed in a player message."""

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


class ILocationService(ABC):
    """Location-specific operations and initialization logic."""

    @abstractmethod
    def validate_traversal(
        self,
        game_state: GameState,
        from_location_id: str,
        to_location_id: str,
    ) -> None:
        """Validate if traversal between locations is allowed.

        Checks if the target location is directly connected from source location
        and if traversal requirements are met.

        Args:
            game_state: Current game state
            from_location_id: ID of location to travel from
            to_location_id: ID of location to travel to

        Raises:
            ValueError: If traversal is not allowed with detailed error message
        """
        pass

    @abstractmethod
    def move_entity(
        self,
        game_state: GameState,
        entity_id: str,
        to_location_id: str,
        location_name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Move any entity (player, NPC, or monster) to a new location.

        Updates location state and initializes scenario-specific content
        if this is the first visit to a scenario location (for player only).

        Args:
            game_state: Game state to update (modified in-place)
            entity_id: ID of entity to move
            to_location_id: New location ID
            location_name: Optional display name for location (player only)
            description: Optional location description (player only)

        Raises:
            ValueError: If entity not found or location invalid
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

    @abstractmethod
    def discover_secret(
        self,
        game_state: GameState,
        secret_id: str,
        secret_description: str | None = None,
    ) -> str:
        """Discover a secret in the current location.

        Args:
            game_state: Game state to update (modified in-place)
            secret_id: ID of the secret to discover
            secret_description: Optional description of the secret

        Returns:
            The resolved secret description

        Raises:
            ValueError: If not in a known location or secret ID is empty
        """
        pass

    @abstractmethod
    def update_location_state(
        self,
        game_state: GameState,
        location_id: str | None = None,
        danger_level: str | None = None,
        complete_encounter: str | None = None,
        add_effect: str | None = None,
    ) -> tuple[str, list[str]]:
        """Update the state of a location.

        Args:
            game_state: Game state to update (modified in-place)
            location_id: Optional location ID (defaults to current)
            danger_level: Optional new danger level
            complete_encounter: Optional encounter ID to mark as complete
            add_effect: Optional effect to add to the location

        Returns:
            Tuple of (resolved_location_id, list_of_updates)

        Raises:
            ValueError: If location unknown or invalid danger level
        """
        pass
