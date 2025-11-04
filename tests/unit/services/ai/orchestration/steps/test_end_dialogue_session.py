"""Tests for EndDialogueSessionIfNeeded step."""

from datetime import datetime

import pytest

from app.agents.core.types import AgentType
from app.models.game_state import DialogueSessionMode
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.end_dialogue_session import EndDialogueSessionIfNeeded
from tests.factories import make_game_state


class TestEndDialogueSessionIfNeeded:
    """Tests for EndDialogueSessionIfNeeded step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.step = EndDialogueSessionIfNeeded()

    @pytest.mark.asyncio
    async def test_no_action_when_npc_targets_present(self) -> None:
        """Test no action when NPC targets present in current request."""
        # Setup: Active dialogue with current NPC targets
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.EXPLICIT_ONLY
        self.game_state.dialogue_session.target_npc_ids = ["npc-1"]
        self.game_state.dialogue_session.started_at = datetime.now()
        self.game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(
            user_message="@npc-1 hello",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=["npc-1"]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.active is True
        assert self.game_state.dialogue_session.target_npc_ids == ["npc-1"]
        assert self.game_state.active_agent == AgentType.NPC

    @pytest.mark.asyncio
    async def test_no_action_when_session_not_active(self) -> None:
        """Test no action when dialogue session not active."""
        self.game_state.dialogue_session.active = False
        self.game_state.active_agent = AgentType.NARRATIVE

        ctx = OrchestrationContext(
            user_message="regular message",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.active is False
        assert self.game_state.active_agent == AgentType.NARRATIVE

    @pytest.mark.asyncio
    async def test_no_action_when_mode_not_explicit_only(self) -> None:
        """Test no action when dialogue mode not EXPLICIT_ONLY."""
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.STICKY
        self.game_state.dialogue_session.target_npc_ids = ["npc-1"]
        self.game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(
            user_message="regular message",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.active is True
        assert self.game_state.active_agent == AgentType.NPC

    @pytest.mark.asyncio
    async def test_ends_session_when_conditions_met(self) -> None:
        """Test ends session when all conditions met."""
        # Setup: Active EXPLICIT_ONLY session, no NPC targets in current request
        started_at = datetime.now()
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.EXPLICIT_ONLY
        self.game_state.dialogue_session.target_npc_ids = ["npc-1"]
        self.game_state.dialogue_session.started_at = started_at
        self.game_state.dialogue_session.last_interaction_at = datetime.now()
        self.game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(
            user_message="regular narrative message",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE

        session = self.game_state.dialogue_session
        assert session.active is False
        assert session.target_npc_ids == []
        assert session.started_at is None
        assert session.last_interaction_at is None
        assert self.game_state.active_agent == AgentType.NARRATIVE

    @pytest.mark.asyncio
    async def test_resets_active_agent_from_npc_to_narrative(self) -> None:
        """Test resets active_agent from NPC to NARRATIVE."""
        # Simulate state after NPC dialogue
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.EXPLICIT_ONLY
        self.game_state.dialogue_session.target_npc_ids = ["npc-1"]
        self.game_state.dialogue_session.started_at = datetime.now()
        self.game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(
            user_message="now do something else",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.active_agent == AgentType.NARRATIVE
        assert self.game_state.dialogue_session.active is False

    @pytest.mark.asyncio
    async def test_clears_multiple_target_npcs(self) -> None:
        """Test clears all target NPCs."""
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.EXPLICIT_ONLY
        self.game_state.dialogue_session.target_npc_ids = ["npc-1", "npc-2", "npc-3"]
        self.game_state.dialogue_session.started_at = datetime.now()
        self.game_state.active_agent = AgentType.NPC

        ctx = OrchestrationContext(
            user_message="regular message",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.dialogue_session.target_npc_ids == []
        assert self.game_state.dialogue_session.active is False

    @pytest.mark.asyncio
    async def test_bug_fix_scenario(self) -> None:
        """Regression test for bug: NPC dialogue -> narrative message.

        After talking to an NPC, the next narrative message should properly
        select NARRATIVE agent and build context, not use NPC agent with empty context.
        """
        # Simulate state after NPC dialogue
        self.game_state.dialogue_session.active = True
        self.game_state.dialogue_session.mode = DialogueSessionMode.EXPLICIT_ONLY
        self.game_state.dialogue_session.target_npc_ids = ["tom"]
        self.game_state.dialogue_session.started_at = datetime.now()
        self.game_state.active_agent = AgentType.NPC

        # New request without NPC targets (narrative message)
        ctx = OrchestrationContext(
            user_message="Scan the tavern",
            game_state=self.game_state,
            flags=OrchestrationFlags(npc_targets=[]),
        )

        result = await self.step.run(ctx)

        # Bug fix: active_agent should be NARRATIVE, not NPC
        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert self.game_state.active_agent == AgentType.NARRATIVE
        assert self.game_state.dialogue_session.active is False
