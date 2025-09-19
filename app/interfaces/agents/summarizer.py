"""Protocol describing summarizer-agent capabilities required by services."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.agents.core.base import ToolFunction
from app.models.game_state import GameState, Message
from app.models.instances.npc_instance import NPCInstance
from app.models.memory import MemoryEventKind, WorldEventContext


class ISummarizerAgent(Protocol):
    """Expose summarization helpers used during agent transitions and memory capture."""

    def get_required_tools(self) -> list[ToolFunction]:
        """Return the tools registered with the summarizer agent.

        Returns:
            List of tool functions the agent expects to register (often empty).
        """
        ...

    async def summarize_for_combat(self, game_state: GameState) -> str:
        """Summarize recent narrative context before combat begins.

        Args:
            game_state: Current game state providing conversation history and location info.

        Returns:
            A concise summary string suitable for seeding the combat agent context.
        """
        ...

    async def summarize_combat_end(self, game_state: GameState) -> str:
        """Summarize the outcome of combat for narrative continuation.

        Args:
            game_state: Current game state containing combat log details.

        Returns:
            A concise summary string the narrative agent can use after combat ends.
        """
        ...

    async def summarize_location_session(
        self,
        game_state: GameState,
        location_id: str,
        messages: Sequence[Message],
    ) -> str:
        """Summarize activity at a location since the previous memory checkpoint.

        Args:
            game_state: Game state providing scenario metadata for the location.
            location_id: Scenario location identifier being summarized.
            messages: Conversation history slice relevant to the location session.

        Returns:
            A short summary string suitable for storing in location memories.
        """
        ...

    async def summarize_npc_interactions(
        self,
        game_state: GameState,
        npc: NPCInstance,
        messages: Sequence[Message],
    ) -> str:
        """Summarize recent interactions with the specified NPC.

        Args:
            game_state: Game state that includes NPC rosters and metadata.
            npc: NPC instance whose interactions are being summarized.
            messages: Conversation history slice referencing the NPC.

        Returns:
            A short summary string suitable for storing in NPC memories.
        """
        ...

    async def summarize_world_update(
        self,
        game_state: GameState,
        event_kind: MemoryEventKind,
        messages: Sequence[Message],
        context: WorldEventContext,
    ) -> str:
        """Summarize story-wide changes for world-memory storage.

        Args:
            game_state: Game state providing global scenario status.
            event_kind: Enumerated trigger describing the world event type.
            messages: Conversation history slice relevant to the event.
            context: Structured metadata to include (quests, locations, NPC ids).

        Returns:
            A short summary string suitable for storing in world memories.
        """
        ...
