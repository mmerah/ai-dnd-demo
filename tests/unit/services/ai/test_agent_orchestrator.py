"""Unit tests for `AgentOrchestrator`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService
from app.interfaces.services.game import ICombatService, IConversationService, IGameService, IMetadataService
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import GameState, MessageRole
from app.models.instances.npc_instance import NPCInstance
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.orchestrator_service import AgentOrchestrator
from tests.factories import make_game_state, make_npc_instance


class _StubAgent(BaseAgent):
    def __init__(self, events: list[StreamEvent]) -> None:
        self.events = events
        self.messages: list[str] = []

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self, user_message: str, game_state: GameState, context: str, stream: bool = True
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

    async def process(
        self, prompt: str, game_state: GameState, context: str, stream: bool = True
    ) -> AsyncIterator[StreamEvent]:
        raise NotImplementedError
        yield  # type: ignore[unreachable]


class _StubNPCAgent(BaseAgent):
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[str] = []
        self.active_npc_id: str | None = None

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        context: str,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        if self.active_npc_id is not None:
            self.calls.append(self.active_npc_id)
        yield StreamEvent(type=StreamEventType.COMPLETE, content=self.reply)

    def prepare_for_npc(self, npc: NPCInstance) -> None:
        self.active_npc_id = npc.instance_id


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
    tool_suggestor_agent = _StubAgent(
        [StreamEvent(type=StreamEventType.COMPLETE, content=ToolSuggestions(suggestions=[]))]
    )
    context_service: MagicMock = create_autospec(IContextService, instance=True)
    context_service.build_context.return_value = ""

    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=summarizer,  # type: ignore[arg-type]
        tool_suggestor_agent=tool_suggestor_agent,  # type: ignore[arg-type]
        context_service=context_service,
        combat_service=combat_service,
        event_bus=event_bus,
        game_service=game_service,
        metadata_service=metadata_service,
        conversation_service=conversation_service,
        agent_lifecycle_service=agent_lifecycle,
    )
    return orchestrator, metadata_service, conversation_service, agent_lifecycle


@pytest.mark.asyncio
async def test_orchestrator_uses_narrative_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    narrative_events = [StreamEvent(type=StreamEventType.COMPLETE, content="done")]
    narrative_agent = _StubAgent(narrative_events)
    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", AsyncMock())

    async def _no_op_prompt(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", _no_op_prompt)

    async def _empty_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if kwargs.get("yield_events"):
            yield StreamEvent(type=StreamEventType.COMPLETE, content="noop")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _empty_combat_loop)

    orchestrator, metadata_service, conversation_service, agent_lifecycle = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    user_message = "hello"
    events = [event async for event in orchestrator.process(user_message, game_state)]

    assert events == narrative_events
    assert narrative_agent.messages == [user_message]
    assert combat_agent.messages == []
    metadata_service.extract_targeted_npcs.assert_called_with(user_message, game_state)
    conversation_service.record_message.assert_not_called()
    agent_lifecycle.get_npc_agent.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_handles_combat_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    narrative_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="narrative"),
        ]
    )
    combat_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="combat"),
        ]
    )
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    combat_service.generate_combat_prompt.return_value = "begin combat"
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    reload_calls: list[bool] = [False]

    def _fake_reload(service: object, state: GameState) -> GameState:
        # first call toggles combat active
        state.combat.is_active = not reload_calls[0]
        reload_calls[0] = True
        return state

    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _fake_reload)
    mock_transition = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", mock_transition)
    mock_system_prompt = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_initial_combat_prompt", mock_system_prompt)

    async def _fake_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if kwargs.get("produce_loop"):
            yield StreamEvent(type=StreamEventType.COMPLETE, content="loop")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _fake_combat_loop)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    events = [event async for event in orchestrator.process("advance", game_state)]

    assert any(evt.content == combat_agent.events[0].content for evt in events)
    mock_transition.assert_awaited()
    combat_service.generate_combat_prompt.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_handles_npc_combat_turns(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    # Combat agent handles player turn then NPC turns
    combat_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="player turn done"),
        ]
    )

    # Store NPC turn events
    npc_turn_events = [
        StreamEvent(type=StreamEventType.COMPLETE, content="goblin attacks"),
        StreamEvent(type=StreamEventType.COMPLETE, content="wolf attacks"),
    ]
    expected_npc_contents = [e.content for e in npc_turn_events]

    narrative_agent = _StubAgent([])
    summarizer = _StubSummarizer()

    # Mock combat service to indicate NPC turns
    combat_service = create_autospec(ICombatService, instance=True)
    combat_service.should_auto_continue.side_effect = [True, True, False]  # Two NPCs then stop
    combat_service.generate_combat_prompt.side_effect = [
        "Goblin's turn!",
        "Wolf's turn!",
    ]

    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.COMBAT)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    # Track combat loop calls
    loop_calls = []

    async def _tracked_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        loop_calls.append(kwargs)
        # Yield NPC events if there are any left
        if npc_turn_events:
            yield npc_turn_events.pop(0)

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _tracked_combat_loop)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    events = [event async for event in orchestrator.process("I attack", game_state)]

    # Should get player turn result and NPC turn results
    assert len(events) >= 2
    assert events[0].content == combat_agent.events[0].content
    assert any(evt.content in expected_npc_contents for evt in events)

    # Combat loop should have been called
    assert len(loop_calls) > 0


@pytest.mark.asyncio
async def test_orchestrator_handles_combat_ending_mid_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that orchestrator handles combat ending during NPC turns."""
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    combat_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="defeat last enemy"),
        ]
    )

    narrative_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="aftermath"),
        ]
    )

    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    # Control combat state during reloads
    reload_count = 0

    def _end_combat_on_reload(service: object, state: GameState) -> GameState:
        nonlocal reload_count
        reload_count += 1
        if reload_count == 3:  # End combat on third reload
            state.combat.is_active = False
            state.active_agent = AgentType.NARRATIVE
        return state

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda gs: gs.active_agent)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _end_combat_on_reload)

    mock_transition = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.transitions.handle_transition", mock_transition)

    mock_system = AsyncMock()
    monkeypatch.setattr("app.services.ai.orchestrator.system_broadcasts.send_system_message", mock_system)

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

    events = [event async for event in orchestrator.process("final strike", game_state)]

    # Should have combat end and narrative aftermath
    assert len(events) >= 2
    assert events[0].content == combat_agent.events[0].content
    assert events[-1].content == narrative_agent.events[0].content

    # Transition should be handled
    mock_transition.assert_awaited_once()
    # System message about continuing narrative
    mock_system.assert_awaited_once()


@pytest.mark.asyncio
async def test_orchestrator_skips_combat_loop_when_not_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that combat loop is skipped when combat is not active."""
    game_state = make_game_state()
    game_state.combat.is_active = False  # No active combat

    narrative_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="exploring"),
        ]
    )

    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    # Track if combat loop is called
    combat_loop_called = False

    async def _tracking_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        nonlocal combat_loop_called
        combat_loop_called = True
        yield StreamEvent(type=StreamEventType.COMPLETE, content="should not see this")

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _tracking_combat_loop)

    orchestrator, metadata_service, conversation_service, agent_lifecycle = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    user_message = "look around"
    events = [event async for event in orchestrator.process(user_message, game_state)]

    # Should only have narrative response
    assert len(events) == 1
    assert events[0].content == narrative_agent.events[0].content

    # Combat loop should not be called
    assert not combat_loop_called

    # Only narrative agent should be used
    assert narrative_agent.messages == [user_message]
    assert combat_agent.messages == []
    metadata_service.extract_targeted_npcs.assert_called_with(user_message, game_state)
    conversation_service.record_message.assert_not_called()
    agent_lifecycle.get_npc_agent.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_handles_multiple_state_reloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test proper handling of multiple state reloads during processing."""
    game_state = make_game_state()

    narrative_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="response"),
        ]
    )

    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)

    # Track reload calls
    reload_states = []

    def _tracking_reload(service: object, state: GameState) -> GameState:
        reload_states.append(state.combat.is_active)
        return state

    # Mock game service to track saves
    save_calls = []
    game_service = create_autospec(IGameService, instance=True)
    game_service.get_game.return_value = game_state
    game_service.save_game.side_effect = lambda gs: save_calls.append(gs)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _tracking_reload)

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

    events = [event async for event in orchestrator.process("test", game_state)]

    assert len(events) == 1
    # Should have at least one reload after agent processing
    assert len(reload_states) >= 1


@pytest.mark.asyncio
async def test_orchestrator_combat_continuation_in_active_combat(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test combat continuation when already in active combat."""
    game_state = make_game_state()
    game_state.combat.is_active = True
    game_state.active_agent = AgentType.COMBAT

    combat_agent = _StubAgent(
        [
            StreamEvent(type=StreamEventType.COMPLETE, content="action completed"),
        ]
    )

    narrative_agent = _StubAgent([])
    summarizer = _StubSummarizer()

    combat_service = create_autospec(ICombatService, instance=True)
    combat_service.should_auto_continue.return_value = True
    combat_service.generate_combat_prompt.return_value = "Next turn!"

    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.COMBAT)

    # Keep combat active through reloads
    def _maintain_combat(service: object, state: GameState) -> GameState:
        state.combat.is_active = True
        return state

    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", _maintain_combat)

    # Track combat loop invocations
    loop_events = [
        StreamEvent(type=StreamEventType.COMPLETE, content="npc turn 1"),
        StreamEvent(type=StreamEventType.COMPLETE, content="npc turn 2"),
    ]
    expected_loop_contents = [e.content for e in loop_events]

    async def _multi_turn_combat_loop(**kwargs: object) -> AsyncIterator[StreamEvent]:
        if loop_events:
            yield loop_events.pop(0)

    monkeypatch.setattr("app.services.ai.orchestrator.combat_loop.run", _multi_turn_combat_loop)

    orchestrator, *_ = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    events = [event async for event in orchestrator.process("continue combat", game_state)]

    # Should get player action and NPC turns
    assert len(events) >= 2
    assert events[0].content == combat_agent.events[0].content
    assert any(evt.content in expected_loop_contents for evt in events)


@pytest.mark.asyncio
async def test_orchestrator_routes_to_npc_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    game_state = make_game_state()
    npc = make_npc_instance(instance_id="npc-1")
    npc.current_location_id = game_state.scenario_instance.current_location_id
    game_state.npcs.append(npc)

    narrative_agent = _StubAgent([])
    combat_agent = _StubAgent([])
    summarizer = _StubSummarizer()
    combat_service = create_autospec(ICombatService, instance=True)
    event_bus = create_autospec(IEventBus, instance=True)
    game_service = create_autospec(IGameService, instance=True)

    monkeypatch.setattr("app.services.ai.orchestrator.agent_router.select", lambda _: AgentType.NARRATIVE)
    monkeypatch.setattr("app.services.ai.orchestrator.state_reload.reload", lambda service, state: state)

    orchestrator, metadata_service, conversation_service, agent_lifecycle = _build_orchestrator(
        narrative_agent,
        combat_agent,
        summarizer,
        combat_service,
        event_bus,
        game_service,
    )

    metadata_service.extract_targeted_npcs.return_value = [npc.instance_id]
    npc_agent = _StubNPCAgent("NPC reply")
    agent_lifecycle.get_npc_agent.return_value = npc_agent

    events = [event async for event in orchestrator.process("@Tom hello", game_state)]

    assert len(events) == 1
    assert events[0].content == "NPC reply"
    conversation_service.record_message.assert_called_once()
    args, kwargs = conversation_service.record_message.call_args
    assert args[0] is game_state
    assert args[1] is MessageRole.PLAYER
    assert kwargs["agent_type"] == AgentType.NPC
    agent_lifecycle.get_npc_agent.assert_called_once()
    called_game_state, called_npc = agent_lifecycle.get_npc_agent.call_args.args
    assert called_game_state is game_state
    assert called_npc is npc
    assert npc_agent.calls == [npc.instance_id]
