"""Interface for location service."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.scenario import ScenarioLocation


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
