"""Service that condenses recent gameplay into structured memories."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.services.memory import IMemoryService
from app.models.game_state import GameState, Message
from app.models.memory import MemoryEntry, MemoryEventKind, MemorySource, WorldEventContext

logger = logging.getLogger(__name__)


class MemoryService(IMemoryService):
    """Summarises conversation history into scoped memories."""

    def __init__(self, summarizer_provider: Callable[[], ISummarizerAgent]) -> None:
        self._summarizer_provider = summarizer_provider

    async def on_location_exit(self, game_state: GameState) -> None:
        scenario_instance = game_state.scenario_instance
        if not scenario_instance.is_in_known_location():
            raise ValueError("Cannot capture location memory: current location is unknown")

        location_id = scenario_instance.current_location_id
        location_name = game_state.location
        since_idx = scenario_instance.last_location_message_index.get(location_id, -1)
        summarizer = self._summarizer()
        indexed_messages = self._select_messages_since_index(
            game_state,
            since_idx,
            location_name=location_name,
        )
        if not indexed_messages:
            return

        messages = [msg for _, msg in indexed_messages]
        summary = await summarizer.summarize_location_session(game_state, location_id, messages)
        if not summary:
            logger.warning("Skipping location memory for %s: summarizer returned empty output", location_id)
            return

        last_idx = indexed_messages[-1][0]
        entry = self._build_entry(
            source=MemorySource.LOCATION,
            summary=summary,
            tags=["session", f"location:{location_id}"],
            location_id=location_id,
            since_timestamp=indexed_messages[0][1].timestamp,
            since_message_index=last_idx,
        )

        location_state = game_state.get_location_state(location_id)
        location_state.location_memories.append(entry)
        scenario_instance.last_location_message_index[location_id] = last_idx

        npc_candidates = [npc for npc in game_state.npcs if npc.current_location_id == location_id]
        for npc in npc_candidates:
            npc_name = npc.sheet.character.name
            npc_since_idx = scenario_instance.last_npc_message_index.get(npc.instance_id, -1)
            npc_indexed_messages = self._select_messages_since_index(
                game_state,
                npc_since_idx,
                location_name=location_name,
                npc_name=npc_name,
                include_context_window=True,
            )
            if not npc_indexed_messages:
                continue

            npc_messages = [msg for _, msg in npc_indexed_messages]
            npc_summary = await summarizer.summarize_npc_interactions(game_state, npc, npc_messages)
            if not npc_summary:
                logger.warning(
                    "Skipping NPC memory for %s (%s): summarizer returned empty output",
                    npc.instance_id,
                    npc_name,
                )
                continue

            npc_last_idx = npc_indexed_messages[-1][0]
            npc_entry = self._build_entry(
                source=MemorySource.NPC,
                summary=npc_summary,
                tags=["npc-session", f"location:{location_id}", f"npc:{npc.instance_id}"],
                location_id=location_id,
                npc_ids=[npc.instance_id],
                since_timestamp=npc_indexed_messages[0][1].timestamp,
                since_message_index=npc_last_idx,
            )
            npc.npc_memories.append(npc_entry)
            scenario_instance.last_npc_message_index[npc.instance_id] = npc_last_idx

    async def on_world_event(
        self,
        game_state: GameState,
        event_kind: MemoryEventKind,
        *,
        tags: list[str] | None = None,
        context: WorldEventContext | None = None,
    ) -> None:
        scenario_instance = game_state.scenario_instance
        since_idx = scenario_instance.last_world_message_index
        indexed_messages = self._select_messages_since_index(game_state, since_idx)
        if not indexed_messages:
            return

        summarizer = self._summarizer()
        messages = [msg for _, msg in indexed_messages]
        context = context or WorldEventContext()
        summary = await summarizer.summarize_world_update(game_state, event_kind, messages, context)
        if not summary:
            logger.warning("Skipping world memory for %s: summarizer returned empty output", event_kind)
            return

        last_idx = indexed_messages[-1][0]
        normalized_tags = ["world", f"event:{event_kind.value}"]
        if tags:
            normalized_tags.extend(tags)

        location_id = context.location_id
        if location_id is None and scenario_instance.is_in_known_location():
            location_id = scenario_instance.current_location_id

        entry = self._build_entry(
            source=MemorySource.WORLD,
            summary=summary,
            tags=normalized_tags,
            location_id=location_id,
            npc_ids=context.npc_ids,
            quest_id=context.quest_id,
            encounter_id=context.encounter_id,
            objective_id=context.objective_id,
            act_id=context.act_id,
            since_timestamp=indexed_messages[0][1].timestamp,
            since_message_index=last_idx,
        )
        scenario_instance.world_memories.append(entry)
        scenario_instance.last_world_message_index = last_idx

    def prune(self, game_state: GameState) -> None:  # pragma: no cover - intentionally empty hook
        # Hook for future retention policies (max entries, expiration, etc.)
        return

    def _summarizer(self) -> ISummarizerAgent:
        return self._summarizer_provider()

    def _select_messages_since_index(
        self,
        game_state: GameState,
        since_idx: int,
        *,
        location_name: str | None = None,
        npc_name: str | None = None,
        include_context_window: bool = False,
    ) -> list[tuple[int, Message]]:
        history = game_state.conversation_history
        if not history:
            return []

        start = max(since_idx + 1, 0)
        matching_indexes: list[int] = []
        for idx in range(start, len(history)):
            message = history[idx]
            if location_name is not None and message.location != location_name:
                continue
            if npc_name is not None and npc_name not in message.npcs_mentioned:
                continue
            matching_indexes.append(idx)

        if not matching_indexes:
            return []

        if include_context_window:
            context_indexes = set(matching_indexes)
            for idx in matching_indexes:
                prev_idx = idx - 1
                if prev_idx > since_idx:
                    prev_message = history[prev_idx]
                    if location_name is None or prev_message.location == location_name:
                        context_indexes.add(prev_idx)
                next_idx = idx + 1
                if next_idx < len(history):
                    next_message = history[next_idx]
                    if location_name is None or next_message.location == location_name:
                        context_indexes.add(next_idx)
            matching_indexes = sorted(context_indexes)

        return [(idx, history[idx]) for idx in matching_indexes]

    @staticmethod
    def _build_entry(
        *,
        source: MemorySource,
        summary: str,
        tags: list[str],
        location_id: str | None,
        since_timestamp: datetime,
        since_message_index: int,
        npc_ids: list[str] | None = None,
        quest_id: str | None = None,
        encounter_id: str | None = None,
        objective_id: str | None = None,
        act_id: str | None = None,
    ) -> MemoryEntry:
        return MemoryEntry(
            source=source,
            summary=summary,
            tags=tags,
            location_id=location_id,
            npc_ids=npc_ids or [],
            quest_id=quest_id,
            encounter_id=encounter_id,
            objective_id=objective_id,
            act_id=act_id,
            since_timestamp=since_timestamp,
            since_message_index=since_message_index,
        )
