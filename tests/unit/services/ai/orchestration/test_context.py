"""Tests for OrchestrationContext and OrchestrationFlags."""

import pytest

from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent, StreamEventType
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from tests.factories import make_game_state


class TestOrchestrationFlags:
    """Tests for OrchestrationFlags."""

    def test_default_flags(self) -> None:
        """Test default flag values."""
        flags = OrchestrationFlags()

        assert flags.combat_was_active is False
        assert flags.npc_targets == []

    def test_flags_with_values(self) -> None:
        """Test creating flags with custom values."""
        flags = OrchestrationFlags(combat_was_active=True, npc_targets=["npc1", "npc2"])

        assert flags.combat_was_active is True
        assert flags.npc_targets == ["npc1", "npc2"]

    def test_flags_with_updates(self) -> None:
        """Test updating flags creates a new instance."""
        flags = OrchestrationFlags(combat_was_active=False, npc_targets=[])
        updated = flags.with_updates(combat_was_active=True, npc_targets=["npc1"])

        # Original unchanged
        assert flags.combat_was_active is False
        assert flags.npc_targets == []

        # Updated instance has new values
        assert updated.combat_was_active is True
        assert updated.npc_targets == ["npc1"]

    def test_flags_partial_update(self) -> None:
        """Test updating only some fields."""
        flags = OrchestrationFlags(combat_was_active=True, npc_targets=["npc1"])
        updated = flags.with_updates(npc_targets=["npc1", "npc2"])

        # Updated field
        assert updated.npc_targets == ["npc1", "npc2"]


class TestOrchestrationContext:
    """Tests for OrchestrationContext."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")

    def test_minimal_context_creation(self) -> None:
        """Test creating context with minimal required fields."""
        ctx = OrchestrationContext(user_message="Hello", game_state=self.game_state)

        assert ctx.user_message == "Hello"
        assert ctx.game_state is self.game_state
        assert ctx.game_id == "test-game"
        assert ctx.incoming_agent_hint is None
        assert ctx.selected_agent_type is None
        assert ctx.context_text == ""
        assert isinstance(ctx.flags, OrchestrationFlags)
        assert ctx.events == []

    def test_context_with_all_fields(self) -> None:
        """Test creating context with all fields populated."""
        flags = OrchestrationFlags(combat_was_active=True, npc_targets=["npc1"])
        event = StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="Test")

        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            incoming_agent_hint=AgentType.COMBAT,
            selected_agent_type=AgentType.COMBAT,
            context_text="Combat context...",
            flags=flags,
            events=[event],
        )

        assert ctx.user_message == "Attack!"
        assert ctx.game_id == "test-game"
        assert ctx.incoming_agent_hint == AgentType.COMBAT
        assert ctx.selected_agent_type == AgentType.COMBAT
        assert ctx.context_text == "Combat context..."
        assert ctx.flags.combat_was_active is True
        assert len(ctx.events) == 1

    def test_context_with_updates(self) -> None:
        """Test updating context creates a new instance."""
        ctx = OrchestrationContext(user_message="Original", game_state=self.game_state)

        updated = ctx.with_updates(selected_agent_type=AgentType.NARRATIVE, context_text="New context")

        # Original unchanged
        assert ctx.selected_agent_type is None
        assert ctx.context_text == ""

        # Updated instance has new values
        assert updated.selected_agent_type == AgentType.NARRATIVE
        assert updated.context_text == "New context"

    def test_add_event(self) -> None:
        """Test adding a single event."""
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

        event1 = StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="First")
        ctx_with_event = ctx.add_event(event1)

        # Original unchanged
        assert len(ctx.events) == 0

        # Updated context has event
        assert len(ctx_with_event.events) == 1
        assert ctx_with_event.events[0] is event1

        # Can add another event
        event2 = StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="Second")
        ctx_with_two = ctx_with_event.add_event(event2)

        assert len(ctx_with_two.events) == 2
        assert ctx_with_two.events[0] is event1
        assert ctx_with_two.events[1] is event2

    def test_add_events(self) -> None:
        """Test adding multiple events at once."""
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

        events = [
            StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="First"),
            StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="Second"),
            StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="Third"),
        ]
        ctx_with_events = ctx.add_events(events)

        # Original unchanged
        assert len(ctx.events) == 0

        # Updated context has all events
        assert len(ctx_with_events.events) == 3
        assert ctx_with_events.events == events

    def test_require_agent_type_success(self) -> None:
        """Test require_agent_type returns type when set."""
        ctx = OrchestrationContext(
            user_message="Test", game_state=self.game_state, selected_agent_type=AgentType.COMBAT
        )

        agent_type = ctx.require_agent_type()

        assert agent_type == AgentType.COMBAT

    def test_require_agent_type_raises_when_not_set(self) -> None:
        """Test require_agent_type raises ValueError when type not selected."""
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

        with pytest.raises(ValueError, match="Agent type not selected"):
            ctx.require_agent_type()

    def test_game_id_derived_from_game_state(self) -> None:
        """Test that game_id is automatically derived from game_state."""
        game_state = make_game_state(game_id="derived-id")
        ctx = OrchestrationContext(user_message="Test", game_state=game_state)

        assert ctx.game_id == "derived-id"
        assert ctx.game_id == game_state.game_id

    def test_flags_update_via_context(self) -> None:
        """Test updating flags through context.with_updates."""
        ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

        assert ctx.flags.npc_targets == []

        updated_flags = ctx.flags.with_updates(npc_targets=["npc1", "npc2"])
        ctx_with_flags = ctx.with_updates(flags=updated_flags)

        # Original unchanged
        assert ctx.flags.npc_targets == []

        # Updated context has new flags
        assert ctx_with_flags.flags.npc_targets == ["npc1", "npc2"]
