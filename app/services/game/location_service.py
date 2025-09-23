"""LocationService: encapsulates location transitions and initialization."""

from __future__ import annotations

import logging

from app.interfaces.services.game import ILocationService, IMonsterManagerService
from app.models.attributes import EntityType
from app.models.game_state import GameState
from app.models.instances.monster_instance import MonsterInstance
from app.models.location import DangerLevel, LocationState
from app.models.scenario import ScenarioLocation, ScenarioMonster

logger = logging.getLogger(__name__)


class LocationService(ILocationService):
    """Default implementation for location-related operations."""

    def __init__(self, monster_manager_service: IMonsterManagerService) -> None:
        self.monster_manager_service = monster_manager_service

    def validate_traversal(
        self,
        game_state: GameState,
        from_location_id: str,
        to_location_id: str,
    ) -> None:
        # Only validate if we're in a known scenario location
        if game_state.scenario_id:
            scenario = game_state.scenario_instance.sheet
            from_location = scenario.get_location(from_location_id)

            if from_location:
                # Check if target location is directly connected from source location
                is_connected = any(conn.to_location_id == to_location_id for conn in from_location.connections)

                if not is_connected:
                    # Check if we can traverse to the target location
                    valid_connections = [
                        conn.to_location_id for conn in from_location.connections if conn.can_traverse()
                    ]
                    raise ValueError(
                        f"Cannot travel to '{to_location_id}' from location '{from_location_id}'. "
                        f"Valid destinations: {valid_connections}"
                    )

    def move_entity(
        self,
        game_state: GameState,
        entity_id: str,
        to_location_id: str,
        location_name: str | None = None,
        description: str | None = None,
    ) -> None:
        # If entity_id matches the player's id, it's the player moving
        if entity_id == game_state.character.instance_id:
            # Prepare resolution based on scenario definitions and current visit state
            scenario_loc = None
            if game_state.scenario_id:
                scenario = game_state.scenario_instance.sheet
                scenario_loc = scenario.get_location(to_location_id)

            # Determine display name
            resolved_name = location_name
            if not resolved_name:
                resolved_name = scenario_loc.name if scenario_loc else to_location_id

            # Determine description
            resolved_desc = description
            if not resolved_desc:
                if scenario_loc:
                    # Use pre-visit state for description variant
                    loc_state = game_state.get_location_state(to_location_id)
                    if not loc_state.visited:
                        variant = "first_visit"
                    else:
                        variant = "cleared" if loc_state.danger_level == DangerLevel.CLEARED else "return_visit"
                    resolved_desc = scenario_loc.get_description(variant)
                else:
                    raise ValueError(
                        "Location description is required for non-scenario locations (provide a short description)."
                    )

            # For ad-hoc locations, ensure name is provided
            if not scenario_loc and not location_name:
                raise ValueError("Location name is required for non-scenario locations (provide a display name).")

            # If first time at a scenario location, initialize scenario state before marking visited
            if scenario_loc:
                pre_state = game_state.get_location_state(to_location_id)
                if not pre_state.visited:
                    self.initialize_location_from_scenario(game_state, scenario_loc)

            # Update game state's current location and mark visited
            # Update location state tracking within scenario instance
            if to_location_id not in game_state.scenario_instance.location_states:
                game_state.scenario_instance.location_states[to_location_id] = LocationState(location_id=to_location_id)
            location_state = game_state.scenario_instance.location_states[to_location_id]
            location_state.mark_visited()
            game_state.scenario_instance.current_location_id = to_location_id
            game_state.location = resolved_name
            game_state.description = resolved_desc
            game_state.add_story_note(f"Moved to {resolved_name}")
        else:
            # Moving an NPC or monster
            npc = game_state.get_npc_by_id(entity_id)
            if npc:
                # Validate target location exists in scenario
                if game_state.scenario_id:
                    scenario = game_state.scenario_instance.sheet
                    target = scenario.get_location(to_location_id)
                    if not target:
                        raise ValueError(f"Target location '{to_location_id}' not found in scenario")

                # Move NPC
                npc.current_location_id = to_location_id
                npc.touch()
            else:
                # Check if it's a monster
                entity = game_state.get_entity_by_id(EntityType.MONSTER, entity_id)
                if entity and isinstance(entity, MonsterInstance):
                    # Validate target location exists in scenario
                    if game_state.scenario_id:
                        scenario = game_state.scenario_instance.sheet
                        target = scenario.get_location(to_location_id)
                        if not target:
                            raise ValueError(f"Target location '{to_location_id}' not found in scenario")

                    # Move monster
                    entity.current_location_id = to_location_id
                else:
                    raise ValueError(f"Entity with id '{entity_id}' not found")

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        location_state = game_state.get_location_state(scenario_location.id)
        if not location_state.visited:
            location_state.danger_level = scenario_location.danger_level

            # Materialize notable monsters present at this location
            if scenario_location.notable_monsters:
                for sm in scenario_location.notable_monsters:
                    if isinstance(sm, ScenarioMonster):
                        inst = self.monster_manager_service.create(
                            sm.monster.model_copy(deep=True),
                            current_location_id=scenario_location.id,
                        )
                        self.monster_manager_service.add_monster_to_game(game_state, inst)

    def discover_secret(
        self,
        game_state: GameState,
        secret_id: str,
        secret_description: str | None = None,
    ) -> str:
        # Validate secret ID
        if not secret_id:
            raise ValueError("Secret ID cannot be empty")

        # Update location state
        if not game_state.scenario_instance.is_in_known_location():
            raise ValueError("Cannot discover secret: current location is unknown")

        current_loc = game_state.scenario_instance.current_location_id
        location_state = game_state.get_location_state(current_loc)
        location_state.discover_secret(secret_id)

        # Use provided description or default to the secret ID
        return secret_description or f"Secret '{secret_id}'"

    def update_location_state(
        self,
        game_state: GameState,
        location_id: str | None = None,
        danger_level: str | None = None,
        complete_encounter: str | None = None,
        add_effect: str | None = None,
    ) -> tuple[str, list[str]]:
        """Update the state of a location."""
        # Use provided location_id or default to current location
        if not location_id:
            if not game_state.scenario_instance.is_in_known_location():
                raise ValueError(
                    "Cannot update location state: current location is unknown and no location_id provided"
                )
            location_id = game_state.scenario_instance.current_location_id
            logger.warning(f"UpdateLocationState: No location_id provided, using current location: {location_id}")

        location_state = game_state.get_location_state(location_id)
        updates = []

        # Update danger level
        if danger_level:
            try:
                location_state.danger_level = DangerLevel(danger_level)
                updates.append(f"Danger level: {danger_level}")
            except ValueError as e:
                raise ValueError(f"Invalid danger level: {danger_level}") from e

        # Complete encounter
        if complete_encounter:
            location_state.complete_encounter(complete_encounter)
            updates.append(f"Completed encounter: {complete_encounter}")

        # Add effect
        if add_effect and add_effect not in location_state.active_effects:
            location_state.active_effects.append(add_effect)
            updates.append(f"Added effect: {add_effect}")

        return location_id, updates
