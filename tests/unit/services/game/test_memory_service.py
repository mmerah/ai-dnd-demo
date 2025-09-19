"""Unit tests for MemoryService."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import cast

import pytest

from app.agents.core.base import ToolFunction
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState, Message, MessageRole
from app.models.instances.npc_instance import NPCInstance
from app.models.memory import MemoryEventKind, WorldEventContext
from app.services.game.memory_service import MemoryService
from tests.factories import make_game_state, make_npc_instance


class _StubSummarizer:
    """Lightweight stub returning deterministic summaries."""

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    async def summarize_location_session(
        self,
        game_state: GameState,
        location_id: str,
        messages: Sequence[Message],
    ) -> str:
        return f"Summary for {location_id}"

    async def summarize_npc_interactions(
        self,
        game_state: GameState,
        npc: NPCInstance,
        messages: Sequence[Message],
    ) -> str:
        return f"NPC summary for {npc.instance_id}"

    async def summarize_world_update(
        self,
        game_state: GameState,
        event_kind: MemoryEventKind,
        messages: Sequence[Message],
        context: WorldEventContext,
    ) -> str:
        return f"World summary: {event_kind.value}"

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:
        if game_state.game_id == "__noop__":
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=""),
            )


@pytest.mark.asyncio
async def test_memory_service_location_exit_creates_entries_and_updates_cursors() -> None:
    game_state = make_game_state(location_id="town-square", location_name="Town Square")
    npc = make_npc_instance(instance_id="npc-1", current_location_id=game_state.scenario_instance.current_location_id)
    game_state.npcs.append(npc)

    game_state.conversation_history.extend(
        [
            Message(
                role=MessageRole.PLAYER,
                content="We search the market stalls.",
                location=game_state.location,
                npcs_mentioned=[],
            ),
            Message(
                role=MessageRole.DM,
                content="The shopkeeper offers a rare trinket.",
                location=game_state.location,
                npcs_mentioned=[npc.sheet.character.name],
            ),
        ]
    )

    service = MemoryService(lambda: cast(ISummarizerAgent, _StubSummarizer()))
    await service.on_location_exit(game_state)

    location_id = game_state.scenario_instance.current_location_id
    location_state = game_state.get_location_state(location_id)
    assert len(location_state.location_memories) == 1
    location_memory = location_state.location_memories[0]
    assert location_memory.summary == f"Summary for {location_id}"
    assert location_memory.since_message_index == len(game_state.conversation_history) - 1
    assert game_state.scenario_instance.last_location_message_index[location_id] == location_memory.since_message_index

    assert len(npc.npc_memories) == 1
    npc_memory = npc.npc_memories[0]
    assert npc_memory.summary == f"NPC summary for {npc.instance_id}"
    assert game_state.scenario_instance.last_npc_message_index[npc.instance_id] == npc_memory.since_message_index


@pytest.mark.asyncio
async def test_memory_service_npc_entries_only_for_present_and_mentioned() -> None:
    game_state = make_game_state(location_id="plaza", location_name="Central Plaza")
    present_npc = make_npc_instance(
        instance_id="npc-present", current_location_id=game_state.scenario_instance.current_location_id
    )
    absent_npc = make_npc_instance(instance_id="npc-away", current_location_id="other-location")
    game_state.npcs.extend([present_npc, absent_npc])

    game_state.conversation_history.append(
        Message(
            role=MessageRole.DM,
            content="A familiar face waves from the crowd.",
            location=game_state.location,
            npcs_mentioned=[present_npc.sheet.character.name],
        )
    )

    service = MemoryService(lambda: cast(ISummarizerAgent, _StubSummarizer()))
    await service.on_location_exit(game_state)

    assert present_npc.npc_memories
    assert absent_npc.npc_memories == []


@pytest.mark.asyncio
async def test_memory_service_world_event_creates_world_memory() -> None:
    game_state = make_game_state(location_id="keep", location_name="Stormkeep")
    game_state.conversation_history.append(
        Message(
            role=MessageRole.PLAYER,
            content="We triumphantly raise the banner.",
            location=game_state.location,
            npcs_mentioned=[],
        )
    )

    service = MemoryService(lambda: cast(ISummarizerAgent, _StubSummarizer()))
    await service.on_world_event(
        game_state,
        event_kind=MemoryEventKind.QUEST_COMPLETED,
        context=WorldEventContext(quest_id="rescue-mission"),
    )

    world_memories = game_state.scenario_instance.world_memories
    assert len(world_memories) == 1
    entry = world_memories[0]
    assert entry.summary == f"World summary: {MemoryEventKind.QUEST_COMPLETED.value}"
    assert entry.quest_id == "rescue-mission"
    assert game_state.scenario_instance.last_world_message_index == len(game_state.conversation_history) - 1
