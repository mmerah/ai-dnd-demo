"""Factory helpers for building GameState instances for tests."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.game_state import GameState
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState

from .characters import make_character_instance, make_character_sheet
from .scenario import make_location, make_scenario


def make_game_state(
    *,
    game_id: str = "game-test",
    character_id: str = "hero",
    location_id: str = "start",
    location_name: str = "Start",
    additional_locations: Sequence[str] | None = None,
) -> GameState:
    """Create a GameState with a single character and scenario."""
    sheet = make_character_sheet(character_id=character_id)
    character = make_character_instance(sheet=sheet, instance_id=f"{character_id}-inst")

    base_location = make_location(
        location_id=location_id,
        name=location_name,
        description=f"Location {location_name}",
    )

    locations = [base_location]
    if additional_locations:
        for loc in additional_locations:
            locations.append(
                make_location(
                    location_id=loc,
                    name=loc.title(),
                    description=f"Location {loc}",
                )
            )

    scenario = make_scenario(
        scenario_id="scenario-test",
        title="Scenario Test",
        description="Scenario for GameState factory",
        starting_location_id=base_location.id,
        locations=locations,
    )
    scenario_instance = ScenarioInstance(
        instance_id="scenario-inst",
        template_id=scenario.id,
        sheet=scenario,
        current_location_id=base_location.id,
    )
    scenario_instance.location_states[base_location.id] = LocationState(location_id=base_location.id)

    return GameState(
        game_id=game_id,
        character=character,
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        scenario_instance=scenario_instance,
        location=base_location.name,
        content_packs=list(scenario.content_packs),
    )
