"""Interfaces for the narrative memory subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.memory import MemoryEventKind, WorldEventContext


class IMemoryService(ABC):
    """Persist and manage structured memories derived from conversation history."""

    @abstractmethod
    async def on_location_exit(self, game_state: GameState) -> None:
        """Summarize the current location session and record NPC memories before moving.

        Args:
            game_state: Mutable game state containing conversation history and scenario data.

        Returns:
            None. Implementations append memory entries directly to the game state.
        """

    @abstractmethod
    async def on_world_event(
        self,
        game_state: GameState,
        event_kind: MemoryEventKind,
        *,
        tags: list[str] | None = None,
        context: WorldEventContext | None = None,
    ) -> None:
        """Summarize major story events and persist them as world-level memories.

        Args:
            game_state: Mutable game state that receives the memory entry.
            event_kind: Enumerated trigger describing the world event.
            tags: Optional custom tags to append to the memory entry.
            context: Structured metadata about related locations and NPCs.

        Returns:
            None. Implementations append memory entries directly to the game state.
        """

    @abstractmethod
    def prune(self, game_state: GameState) -> None:
        """Apply retention policies to existing memories when required.

        Args:
            game_state: Game state containing memories subject to pruning.

        Returns:
            None. Implementations mutate the game state's memory collections as needed.
        """
