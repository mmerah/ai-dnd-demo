from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class MonstersAtLocationContextBuilder(ContextBuilder):
    """Build context for monsters present at the current location (runtime instances)."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        current_loc_id = game_state.scenario_instance.current_location_id
        monsters_here = [m for m in game_state.monsters if m.current_location_id == current_loc_id and m.is_alive()]
        if not monsters_here:
            return None

        lines = ["Monsters Present (use IDs for tools):"]
        for m in monsters_here:
            st = m.state
            lines.append(
                f"  • {m.sheet.name} [ID: {m.instance_id}]: HP {st.hit_points.current}/{st.hit_points.maximum}, AC {st.armor_class}"
            )

        return "\n".join(lines)
