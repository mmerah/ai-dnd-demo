"""Builder for scenario header and current location context."""

from app.models.game_state import GameState

from .base import ContextBuilder


class ScenarioContextBuilder(ContextBuilder):
    """Build scenario header with title, description, and current location info."""

    def build(self, game_state: GameState) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        scenario = game_state.scenario_instance.sheet
        location_id = game_state.scenario_instance.current_location_id
        location = scenario.get_location(location_id)
        location_state = game_state.get_location_state(location_id)
        context_parts = [f"# {scenario.title}", "", scenario.description, ""]

        if location:
            context_parts.append(f"## Current Location: {location.name}")
            context_parts.append(location.description)
            context_parts.append("")

            if location.encounter_ids:
                uncompleted_encounters = [
                    eid for eid in location.encounter_ids if eid not in location_state.completed_encounters
                ]

                if uncompleted_encounters:
                    context_parts.append(f"Potential encounters: {len(uncompleted_encounters)} available")

                    for enc_id in uncompleted_encounters[:3]:
                        encounter = scenario.get_encounter_by_id(enc_id)
                        if encounter:
                            context_parts.append(f"  - [{enc_id}] {encounter.type}: {encounter.difficulty} difficulty")

                    if len(uncompleted_encounters) > 3:
                        context_parts.append(f"  ... and {len(uncompleted_encounters) - 3} more")

                    context_parts.append("")

        return "\n".join(context_parts)
