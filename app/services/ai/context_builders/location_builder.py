import logging

from app.models.game_state import GameState
from app.models.scenario import ScenarioSheet

from .base import BuildContext, ContextBuilder

logger = logging.getLogger(__name__)


class LocationContextBuilder(ContextBuilder):
    """Build enhanced location context with connections, encounters, and loot."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        scenario: ScenarioSheet = game_state.scenario_instance.sheet
        loc_id = game_state.scenario_instance.current_location_id

        location = scenario.get_location(loc_id)
        if not location:
            return None

        location_state = game_state.get_location_state(loc_id)
        context_parts = ["Enhanced Location Details:"]

        context_parts.append(f"- Current Location ID: {loc_id}")
        context_parts.append(f"- Danger Level: {location_state.danger_level.value}")
        context_parts.append(f"- Visited: {location_state.times_visited} time(s)")

        if location.connections:
            context_parts.append("\nAvailable Exits:")
            for conn in location.connections:
                if conn.is_visible:
                    target_loc = scenario.get_location(conn.to_location_id)
                    if target_loc:
                        exit_desc = f"  - {conn.description} to {target_loc.name} [ID: {conn.to_location_id}]"
                        if conn.requirements:
                            req_status = "✓" if conn.can_traverse() else "✗"
                            exit_desc += f" [{req_status}]"
                        context_parts.append(exit_desc)

        if location.notable_monsters:
            context_parts.append("\nNotable Threats:")
            for nm in location.notable_monsters:
                try:
                    context_parts.append(f"  - {nm.display_name}: {nm.description or ''}")
                except Exception:
                    continue

        uncompleted_encounter_ids = [
            eid for eid in location.encounter_ids if eid not in location_state.completed_encounters
        ]
        if uncompleted_encounter_ids:
            context_parts.append("\nPotential Encounters:")
            for eid in uncompleted_encounter_ids[:5]:
                enc = scenario.get_encounter_by_id(eid)
                if enc:
                    context_parts.append(f"  - {enc.type} [ID: {enc.id}]: {enc.description[:50]}...")

        if location.loot_table:
            available_loot = [loot for loot in location.loot_table if not loot.found]
            if available_loot:
                context_parts.append("\nPotential Items (not yet found):")
                for loot in available_loot[:3]:
                    # AI game master should see all items including hidden ones
                    # Only show items that exist in the repository
                    if context.item_repository.validate_reference(loot.item_index):
                        hidden_marker = " [HIDDEN]" if loot.hidden else ""
                        context_parts.append(f"  - {loot.item_index} (exact ID) {hidden_marker}")
                    else:
                        logger.warning(f"Item '{loot.item_index}' in location loot table not found in item repository")

        return "\n".join(context_parts)
