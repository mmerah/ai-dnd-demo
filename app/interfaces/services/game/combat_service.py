"""Interface for combat service."""

from abc import ABC, abstractmethod

from app.models.combat import CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameState
from app.models.location import EncounterParticipantSpawn


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

    @abstractmethod
    def start_combat(self, game_state: GameState) -> CombatState:
        """Initialize combat state.

        Creates a new combat state and increments the combat occurrence counter.
        This method encapsulates the business logic previously in GameState.

        Args:
            game_state: The game state to update

        Returns:
            The newly created combat state
        """
        pass

    @abstractmethod
    def end_combat(self, game_state: GameState) -> None:
        """End current combat encounter.

        Deactivates combat, removes dead monsters, and resets combat participants.
        This method encapsulates the business logic previously in GameState.

        Args:
            game_state: The game state to update
        """
        pass
