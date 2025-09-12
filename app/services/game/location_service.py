"""LocationService: encapsulates location transitions and initialization."""

from __future__ import annotations

from app.interfaces.services.game import ILocationService, IMonsterFactory
from app.models.game_state import GameState
from app.models.location import DangerLevel
from app.models.scenario import ScenarioLocation, ScenarioMonster


class LocationService(ILocationService):
    """Default implementation for location-related operations."""

    def __init__(self, monster_factory: IMonsterFactory) -> None:
        self.monster_factory = monster_factory

    def change_location(
        self,
        game_state: GameState,
        location_id: str,
        location_name: str | None,
        description: str | None,
    ) -> None:
        # Prepare resolution based on scenario definitions and current visit state
        scenario_loc = None
        if game_state.scenario_id:
            scenario = game_state.scenario_instance.sheet
            scenario_loc = scenario.get_location(location_id)

        # Determine display name
        resolved_name = location_name
        if not resolved_name:
            resolved_name = scenario_loc.name if scenario_loc else location_id

        # Determine description
        resolved_desc = description
        if not resolved_desc:
            if scenario_loc:
                # Use pre-visit state for description variant
                loc_state = game_state.get_location_state(location_id)
                if not loc_state.visited:
                    variant = "first_visit"
                else:
                    variant = "cleared" if loc_state.danger_level == DangerLevel.CLEARED else "return_visit"
                resolved_desc = scenario_loc.get_description(variant)
            else:
                # Ad-hoc locations must supply a description
                raise ValueError(
                    "Location description is required for non-scenario locations (provide a short description)."
                )

        # For ad-hoc locations, ensure name is provided
        if not scenario_loc and not location_name:
            raise ValueError("Location name is required for non-scenario locations (provide a display name).")

        # If first time at a scenario location, initialize scenario state before marking visited
        if scenario_loc:
            pre_state = game_state.get_location_state(location_id)
            if not pre_state.visited:
                self.initialize_location_from_scenario(game_state, scenario_loc)

        # Update game state's current location and mark visited
        game_state.change_location(
            new_location_id=location_id,
            new_location_name=resolved_name,
            description=resolved_desc,
        )

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        location_state = game_state.get_location_state(scenario_location.id)
        if not location_state.visited:
            location_state.danger_level = scenario_location.danger_level

            # Materialize notable monsters present at this location
            if scenario_location.notable_monsters:
                for sm in scenario_location.notable_monsters:
                    if isinstance(sm, ScenarioMonster):
                        inst = self.monster_factory.create(
                            sm.monster.model_copy(deep=True),
                            current_location_id=scenario_location.id,
                        )
                        game_state.add_monster_instance(inst)
