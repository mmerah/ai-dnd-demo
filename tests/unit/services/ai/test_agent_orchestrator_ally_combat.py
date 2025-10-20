"""Unit tests for AgentOrchestrator ally combat turn handling."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.interfaces.services.game import ICombatService, IConversationService, IGameService, IMetadataService
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant
from app.models.game_state import GameState
from app.services.ai.orchestrator_service import AgentOrchestrator
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class _StubAgent(BaseAgent):
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events
        self.messages: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self, user_message: str, game_state: GameState, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        self.messages.append(user_message)
        for event in self.events:
            yield event


class _StubSummarizer(BaseAgent):
    async def summarize_for_combat(self, game_state: GameState) -> str:
        return "combat summary"

    async def summarize_combat_end(self, game_state: GameState) -> str:
        return "combat end summary"

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(self, prompt: str, game_state: GameState, stream: bool = True) -> AsyncIterator[StreamEvent]:  # type: ignore[override]
        raise NotImplementedError


def _build_orchestrator(
    narrative_agent: BaseAgent,
    combat_agent: BaseAgent,
    summarizer: _StubSummarizer,
    combat_service: ICombatService,
    event_bus: IEventBus,
    game_service: IGameService,
) -> tuple[AgentOrchestrator, MagicMock, MagicMock, MagicMock]:
    metadata_service: MagicMock = create_autospec(IMetadataService, instance=True)
    metadata_service.extract_targeted_npcs.return_value = []
    conversation_service: MagicMock = create_autospec(IConversationService, instance=True)
    agent_lifecycle: MagicMock = create_autospec(IAgentLifecycleService, instance=True)

    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer,  # type: ignore[arg-type]
        combat_service=combat_service,
        event_bus=event_bus,
        game_service=game_service,
        metadata_service=metadata_service,
        conversation_service=conversation_service,
        agent_lifecycle_service=agent_lifecycle,
    )
    return orchestrator, metadata_service, conversation_service, agent_lifecycle


@pytest.mark.asyncio
async def test_wraps_ally_turn_with_ally_action_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ally NPC turns get wrapped with [ALLY_ACTION] instruction."""
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    # Create NPC and add to party
    npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Eldrin")
    npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
    game_state.npcs.append(npc)
    game_state.party.member_ids.append(npc.instance_id)

    # Set up combat with ally turn
    game_state.combat.participants.append(
        CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=15,
            is_player=False,
            is_active=True,
        )
    )
    game_state.combat.turn_index = 0

    # Track what message the combat agent receives
    combat_agent = _StubAgent([StreamEvent(type=StreamEventType.COMPLETE, content="combat response")])
    narrative_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.COMBAT)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    async def _empty_combat_loop(**_kwargs: object) -> AsyncIterator[StreamEvent]:
        return
        yield

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _empty_combat_loop)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    user_message = "Attack the goblin!"
    _ = [event async for event in orchestrator.process(user_message, game_state)]

    # Verify combat agent received wrapped message
    assert len(combat_agent.messages) == 1
    received_message = combat_agent.messages[0]
    assert received_message.startswith("[ALLY_ACTION]")
    assert npc.display_name in received_message
    assert user_message in received_message
    assert "CALL next_turn immediately once resolved" in received_message


@pytest.mark.asyncio
async def test_raises_when_ally_npc_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fail-fast when allied NPC is missing from game state."""
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    # Set up combat with ally turn for NPC that doesn't exist
    game_state.combat.participants.append(
        CombatParticipant(
            entity_id="nonexistent-npc",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name="Ghost NPC",
            initiative=15,
            is_player=False,
            is_active=True,
        )
    )
    game_state.combat.turn_index = 0

    combat_agent = _StubAgent([])
    narrative_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.COMBAT)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    # Should raise ValueError
    with pytest.raises(ValueError, match="Allied NPC nonexistent-npc not found"):
        _ = [event async for event in orchestrator.process("Attack!", game_state)]


@pytest.mark.asyncio
async def test_raises_when_ally_not_in_party(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fail-fast when NPC has ALLY faction but is not in party."""
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    # Create NPC but DON'T add to party
    npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Eldrin")
    npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
    game_state.npcs.append(npc)
    # Note: NOT added to party!

    # Set up combat with ally turn
    game_state.combat.participants.append(
        CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=15,
            is_player=False,
            is_active=True,
        )
    )
    game_state.combat.turn_index = 0

    combat_agent = _StubAgent([])
    narrative_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.COMBAT)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    # Should raise ValueError
    with pytest.raises(ValueError, match="has ALLY faction in combat but is not in the party"):
        _ = [event async for event in orchestrator.process("Attack!", game_state)]


@pytest.mark.asyncio
async def test_combat_start_skips_prompt_for_ally_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that combat agent is NOT prompted when first turn is an ally."""
    game_state = make_game_state()
    game_state.combat.is_active = False  # Combat not started yet
    game_state.active_agent = AgentType.NARRATIVE

    # Create NPC and add to party
    npc_sheet = make_npc_sheet(npc_id="ally-1", display_name="Eldrin")
    npc = make_npc_instance(instance_id="npc-ally-1", scenario_npc_id="ally-1", npc_sheet=npc_sheet)
    game_state.npcs.append(npc)
    game_state.party.member_ids.append(npc.instance_id)

    # Set up combat to start with ally turn
    game_state.combat.participants.append(
        CombatParticipant(
            entity_id=npc.instance_id,
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name=npc.display_name,
            initiative=20,  # Highest initiative
            is_player=False,
            is_active=True,
        )
    )
    game_state.combat.turn_index = 0

    narrative_agent = _StubAgent([StreamEvent(type=StreamEventType.COMPLETE, content="narrative")])
    combat_agent = _StubAgent([])  # Should NOT be called!
    summarizer = _StubSummarizer()

    combat_service = create_autospec(ICombatService, instance=True)
    combat_service.generate_combat_prompt.return_value = "Begin combat!"
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)

    # Toggle combat on first reload
    reload_calls = [False]

    def _toggle_combat(service: object, state: GameState) -> GameState:
        if not reload_calls[0]:
            state.combat.is_active = True
            reload_calls[0] = True
        return state

    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _toggle_combat)
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", AsyncMock())
    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", AsyncMock())

    # Track if combat loop was called
    combat_loop_called = False

    async def _track_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        nonlocal combat_loop_called
        combat_loop_called = True
        yield StreamEvent(type=StreamEventType.COMPLETE, content="suggestion generated")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _track_combat_loop)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    _ = [event async for event in orchestrator.process("Start combat!", game_state)]

    # Combat agent should NOT be called for ally turn
    assert len(combat_agent.messages) == 0

    # Combat loop should be called (to generate suggestion)
    assert combat_loop_called
