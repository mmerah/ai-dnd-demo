"""Context builder exposing scenario-wide memories."""

from __future__ import annotations

from datetime import datetime

from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder


class WorldMemoryContextBuilder(ContextBuilder):
    """Render recent world-level memories."""

    MAX_ENTRIES = 3

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        world_memories = game_state.scenario_instance.world_memories
        if not world_memories:
            return None

        entries = world_memories[-self.MAX_ENTRIES :]
        lines = ["World Memory Highlights:"]
        for entry in reversed(entries):
            timestamp = self._format_timestamp(entry.created_at)
            lines.append(f"- [{timestamp}] {entry.summary}")
        return "\n".join(lines)

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M")
