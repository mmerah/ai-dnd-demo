"""Context builder exposing recent location memories."""

from __future__ import annotations

from datetime import datetime

from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class LocationMemoryContextBuilder(ContextBuilder):
    """Render recent location memories for the current location."""

    MAX_ENTRIES = 3

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        if not game_state.scenario_instance.is_in_known_location():
            return None

        location_id = game_state.scenario_instance.current_location_id
        location_state = game_state.get_location_state(location_id)
        if not location_state.location_memories:
            return None

        entries = location_state.location_memories[-self.MAX_ENTRIES :]
        lines = [f"Recent Location Memories ({game_state.location}):"]
        for entry in reversed(entries):
            timestamp = self._format_timestamp(entry.created_at)
            lines.append(f"- [{timestamp}] {entry.summary}")
        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M")
