"""Tests for NPC dialogue orchestration steps."""

from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import create_autospec

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.interfaces.services.ai import IAgentLifecycleService
from app.interfaces.services.game import IConversationService, IMetadataService
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import DialogueSessionMode, GameState, MessageRole
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.orchestration.context import (
    OrchestrationContext,
    OrchestrationFlags,
)
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.begin_dialogue_session import (
    BeginDialogueSession,
)
from app.services.ai.orchestration.steps.detect_npc_dialogue import (
    DetectNpcDialogueTargets,
)
from app.services.ai.orchestration.steps.execute_npc_dialogue import ExecuteNpcDialogue
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


class _StubNPCAgent(BaseAgent):
    """Stub NPC agent for testing that supports prepare_for_npc."""

    def __init__(self, response_content: str = "Hello player!") -> None:
        self.response_content = response_content
        self.prepared_npcs: list[NPCInstance] = []

    def prepare_for_npc(self, npc: NPCInstance) -> None:
        """Mock prepare method required by NPC agents."""
        self.prepared_npcs.append(npc)

    def get_required_tools(self) -> list[ToolFunction]:
        """Return empty tools list."""
        return []

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        context: str,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Yield a single narrative chunk event."""
        yield StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content=self.response_content)


class TestDetectNpcDialogueTargets:
    """Tests for DetectNpcDialogueTargets step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.metadata_service = create_autospec(IMetadataService, instance=True)
        self.step = DetectNpcDialogueTargets(self.metadata_service)

    @pytest.mark.asyncio
    async def test_no_npc_targets(self) -> None:
        """Test when no NPCs are targeted in message."""
        self.metadata_service.extract_targeted_npcs.return_value = []

        ctx = OrchestrationContext(
            user_message="I look around the room",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.flags.npc_targets == []
        self.metadata_service.extract_targeted_npcs.assert_called_once_with("I look around the room", self.game_state)

    @pytest.mark.asyncio
    async def test_single_npc_target(self) -> None:
        """Test when a single NPC is targeted."""
        npc_id = "npc-tom-123"
        self.metadata_service.extract_targeted_npcs.return_value = [npc_id]

        ctx = OrchestrationContext(
            user_message="@Tom hello there",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.flags.npc_targets == [npc_id]
        self.metadata_service.extract_targeted_npcs.assert_called_once_with("@Tom hello there", self.game_state)

    @pytest.mark.asyncio
    async def test_multiple_npc_targets(self) -> None:
        """Test when multiple NPCs are targeted."""
        npc_ids = ["npc-tom-123", "npc-sara-456"]
        self.metadata_service.extract_targeted_npcs.return_value = npc_ids

        ctx = OrchestrationContext(
            user_message="@Tom @Sara can you help?",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.flags.npc_targets == npc_ids

    @pytest.mark.asyncio
    async def test_unknown_npc_raises_error(self) -> None:
        """Test that unknown NPC names raise ValueError."""
        self.metadata_service.extract_targeted_npcs.side_effect = ValueError("Unknown NPC target(s): UnknownNPC")

        ctx = OrchestrationContext(
            user_message="@UnknownNPC hello",
            game_state=self.game_state,
        )

        with pytest.raises(ValueError, match="Unknown NPC target"):
            await self.step.run(ctx)


class TestBeginDialogueSession:
    """Tests for BeginDialogueSession step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.step = BeginDialogueSession()

    @pytest.mark.asyncio
    async def test_initializes_dialogue_session(self) -> None:
        """Test that dialogue session is properly initialized."""
        npc_id = "npc-tom-123"
        flags = OrchestrationFlags(npc_targets=[npc_id])
        ctx = OrchestrationContext(
            user_message="@Tom hello",
            game_state=self.game_state,
            flags=flags,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.active is True
        assert self.game_state.dialogue_session.mode == DialogueSessionMode.EXPLICIT_ONLY
        assert self.game_state.dialogue_session.target_npc_ids == [npc_id]
        assert self.game_state.dialogue_session.started_at is not None
        assert self.game_state.dialogue_session.last_interaction_at is not None
        assert self.game_state.active_agent == AgentType.NPC

    @pytest.mark.asyncio
    async def test_updates_existing_session(self) -> None:
        """Test updating an existing dialogue session."""
        # Set up existing session
        existing_started_at = datetime(2024, 1, 1, 12, 0, 0)
        self.game_state.dialogue_session.started_at = existing_started_at
        self.game_state.dialogue_session.active = True

        new_npc_id = "npc-sara-456"
        flags = OrchestrationFlags(npc_targets=[new_npc_id])
        ctx = OrchestrationContext(
            user_message="@Sara hi",
            game_state=self.game_state,
            flags=flags,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        # started_at should not change if already set
        assert self.game_state.dialogue_session.started_at == existing_started_at
        # Other fields should update
        assert self.game_state.dialogue_session.target_npc_ids == [new_npc_id]
        assert self.game_state.dialogue_session.last_interaction_at is not None

    @pytest.mark.asyncio
    async def test_handles_multiple_targets(self) -> None:
        """Test handling multiple NPC targets."""
        npc_ids = ["npc-tom-123", "npc-sara-456"]
        flags = OrchestrationFlags(npc_targets=npc_ids)
        ctx = OrchestrationContext(
            user_message="@Tom @Sara hello both",
            game_state=self.game_state,
            flags=flags,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.target_npc_ids == npc_ids

    @pytest.mark.asyncio
    async def test_no_op_when_no_targets(self) -> None:
        """Test that step is no-op when called without NPC targets."""
        ctx = OrchestrationContext(
            user_message="I look around",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        # Session should not be modified
        assert self.game_state.dialogue_session.active is False


class TestExecuteNpcDialogue:
    """Tests for ExecuteNpcDialogue step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.agent_lifecycle_service = create_autospec(IAgentLifecycleService, instance=True)
        self.conversation_service = create_autospec(IConversationService, instance=True)
        self.step = ExecuteNpcDialogue(
            self.agent_lifecycle_service,
            self.conversation_service,
        )

        # Create test NPC
        npc_sheet = make_npc_sheet(npc_id="npc-tom", display_name="Tom")
        self.npc = make_npc_instance(
            npc_sheet=npc_sheet,
            instance_id="npc-tom-123",
            current_location_id=self.game_state.scenario_instance.current_location_id,
        )
        self.game_state.npcs.append(self.npc)

    def _make_mock_npc_agent(self, response_content: str = "Hello player!") -> _StubNPCAgent:
        """Create a mock NPC agent that yields a response event."""
        return _StubNPCAgent(response_content)

    @pytest.mark.asyncio
    async def test_executes_single_npc_dialogue(self) -> None:
        """Test executing dialogue with a single NPC."""
        mock_agent = self._make_mock_npc_agent("Hello player!")
        self.agent_lifecycle_service.get_npc_agent.return_value = mock_agent

        flags = OrchestrationFlags(npc_targets=[self.npc.instance_id])
        ctx = OrchestrationContext(
            user_message="@Tom hello",
            game_state=self.game_state,
            flags=flags,
        )

        result = await self.step.run(ctx)

        # Verify outcome is HALT
        assert result.outcome == OrchestrationOutcome.HALT
        assert result.reason == "NPC dialogue completed"

        # Verify conversation was recorded
        self.conversation_service.record_message.assert_called_once_with(
            self.game_state,
            MessageRole.PLAYER,
            "@Tom hello",
            agent_type=AgentType.NPC,
        )

        # Verify NPC agent was retrieved and prepared
        self.agent_lifecycle_service.get_npc_agent.assert_called_once_with(self.game_state, self.npc)
        assert len(mock_agent.prepared_npcs) == 1
        assert mock_agent.prepared_npcs[0] is self.npc

        # Verify events were accumulated
        assert len(result.context.events) == 1
        assert result.context.events[0].content == "Hello player!"

    @pytest.mark.asyncio
    async def test_executes_multiple_npc_dialogue(self) -> None:
        """Test executing dialogue with multiple NPCs."""
        # Create second NPC
        npc_sheet2 = make_npc_sheet(npc_id="npc-sara", display_name="Sara")
        npc2 = make_npc_instance(
            npc_sheet=npc_sheet2,
            instance_id="npc-sara-456",
            current_location_id=self.game_state.scenario_instance.current_location_id,
        )
        self.game_state.npcs.append(npc2)

        # Create mock agents
        agent1 = self._make_mock_npc_agent("Tom says hi!")
        agent2 = self._make_mock_npc_agent("Sara waves!")

        self.agent_lifecycle_service.get_npc_agent.side_effect = [agent1, agent2]

        flags = OrchestrationFlags(npc_targets=[self.npc.instance_id, npc2.instance_id])
        ctx = OrchestrationContext(
            user_message="@Tom @Sara hello",
            game_state=self.game_state,
            flags=flags,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.HALT
        assert len(result.context.events) == 2
        assert result.context.events[0].content == "Tom says hi!"
        assert result.context.events[1].content == "Sara waves!"

        # Both agents should be called
        assert self.agent_lifecycle_service.get_npc_agent.call_count == 2
        assert len(agent1.prepared_npcs) == 1
        assert agent1.prepared_npcs[0] is self.npc
        assert len(agent2.prepared_npcs) == 1
        assert agent2.prepared_npcs[0] is npc2

    @pytest.mark.asyncio
    async def test_npc_not_found_raises_error(self) -> None:
        """Test that missing NPC raises ValueError."""
        flags = OrchestrationFlags(npc_targets=["npc-unknown-999"])
        ctx = OrchestrationContext(
            user_message="@Unknown hello",
            game_state=self.game_state,
            flags=flags,
        )

        with pytest.raises(ValueError, match="NPC with id 'npc-unknown-999' not found"):
            await self.step.run(ctx)

    @pytest.mark.asyncio
    async def test_updates_session_timestamp(self) -> None:
        """Test that dialogue session timestamp is updated."""
        mock_agent = self._make_mock_npc_agent()
        self.agent_lifecycle_service.get_npc_agent.return_value = mock_agent

        initial_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        self.game_state.dialogue_session.last_interaction_at = initial_timestamp

        flags = OrchestrationFlags(npc_targets=[self.npc.instance_id])
        ctx = OrchestrationContext(
            user_message="@Tom hello",
            game_state=self.game_state,
            flags=flags,
        )

        await self.step.run(ctx)

        # Timestamp should be updated
        assert self.game_state.dialogue_session.last_interaction_at != initial_timestamp
        assert self.game_state.dialogue_session.last_interaction_at is not None

    @pytest.mark.asyncio
    async def test_passes_empty_context_to_npc_agent(self) -> None:
        """Test that empty context is passed to NPC agents."""

        # Create a custom stub agent that tracks arguments
        class _TrackingAgent(_StubNPCAgent):
            def __init__(self) -> None:
                super().__init__("Response")
                self.process_calls: list[dict[str, str | bool]] = []

            async def process(
                self,
                user_message: str,
                game_state: GameState,
                context: str,
                stream: bool = True,
            ) -> AsyncIterator[StreamEvent]:
                self.process_calls.append({"msg": user_message, "context": context, "stream": stream})
                async for event in super().process(user_message, game_state, context, stream):
                    yield event

        tracking_agent = _TrackingAgent()
        self.agent_lifecycle_service.get_npc_agent.return_value = tracking_agent

        flags = OrchestrationFlags(npc_targets=[self.npc.instance_id])
        ctx = OrchestrationContext(
            user_message="@Tom hello",
            game_state=self.game_state,
            flags=flags,
        )

        await self.step.run(ctx)

        # Verify empty context was passed
        assert len(tracking_agent.process_calls) == 1
        assert tracking_agent.process_calls[0]["context"] == ""
        assert tracking_agent.process_calls[0]["stream"] is True

    @pytest.mark.asyncio
    async def test_no_op_when_no_targets(self) -> None:
        """Test that step halts gracefully when called without NPC targets."""
        ctx = OrchestrationContext(
            user_message="I look around",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.HALT
        assert result.reason == "No NPC targets to process"
        self.conversation_service.record_message.assert_not_called()
        self.agent_lifecycle_service.get_npc_agent.assert_not_called()
