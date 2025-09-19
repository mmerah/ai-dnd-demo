"""Context builder exposing recent NPC memories at the current location."""

from __future__ import annotations

from datetime import datetime

from app.models.game_state import GameState

from .base import ContextBuilder


class NPCMemoryContextBuilder(ContextBuilder):
    """Render memory snippets for NPCs sharing the player's location."""

    MAX_ENTRIES = 3

    def build(self, game_state: GameState) -> str | None:
        if not game_state.npcs or not game_state.scenario_instance.is_in_known_location():
            return None

        location_id = game_state.scenario_instance.current_location_id
        sections: list[str] = []
        for npc in game_state.npcs:
            if npc.current_location_id != location_id or not npc.npc_memories:
                continue

            entries = npc.npc_memories[-self.MAX_ENTRIES :]
            lines = [f"- {npc.display_name}:"]
            for entry in reversed(entries):
                timestamp = self._format_timestamp(entry.created_at)
                lines.append(f"  - [{timestamp}] {entry.summary}")
            sections.append("\n".join(lines))

        if not sections:
            return None

        header = "NPC Memory Highlights:"
        return "\n".join([header, *sections])

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M")
