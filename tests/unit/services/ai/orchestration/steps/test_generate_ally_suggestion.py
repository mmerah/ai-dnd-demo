"""Tests for GenerateAllySuggestion step."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import Mock, create_autospec

import pytest

from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.generate_ally_suggestion import (
    GenerateAllySuggestion,
)
from tests.factories import (
    make_combat_participant,
    make_combat_state,
    make_game_state,
    make_npc_instance,
)


class TestGenerateAllySuggestion:
    """Tests for GenerateAllySuggestion step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.agent_lifecycle = create_autospec(IAgentLifecycleService, instance=True)
        self.event_bus = create_autospec(IEventBus, instance=True)

        self.step = GenerateAllySuggestion(
            agent_lifecycle_service=self.agent_lifecycle,
            event_bus=self.event_bus,
        )

        self.game_state = make_game_state(game_id="test-game")
        self.game_state.combat = make_combat_state(is_active=True)

    @pytest.mark.asyncio
    async def test_no_op_when_combat_not_active(self) -> None:
        """Test step returns CONTINUE when combat is not active."""
        self.game_state.combat.is_active = False
        ctx = OrchestrationContext(user_message="Hello", game_state=self.game_state)

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        self.agent_lifecycle.get_npc_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_op_when_no_current_turn(self) -> None:
        """Test step returns CONTINUE when no current turn exists."""
        self.game_state.combat.participants = []
        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        self.agent_lifecycle.get_npc_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_npc_not_found(self) -> None:
        """Test step raises ValueError when NPC entity not found in game state."""
        ally = make_combat_participant(
            entity_id="npc-missing-123",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            initiative=20,
        )
        self.game_state.combat.participants = [ally]
        self.game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        with pytest.raises(ValueError, match="NPC.*not found"):
            await self.step.run(ctx)

    @pytest.mark.asyncio
    async def test_raises_when_npc_not_in_party(self) -> None:
        """Test step raises ValueError when NPC is not in party."""
        npc = make_npc_instance(instance_id="npc-tom-123")
        self.game_state.npcs.append(npc)

        ally = make_combat_participant(
            entity_id="npc-tom-123",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            initiative=20,
        )
        self.game_state.combat.participants = [ally]
        self.game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        with pytest.raises(ValueError, match="not in the party"):
            await self.step.run(ctx)

    @pytest.mark.asyncio
    async def test_generates_and_broadcasts_suggestion(self) -> None:
        """Test step generates suggestion and broadcasts it, returning HALT."""
        npc = make_npc_instance(instance_id="npc-tom-123")
        self.game_state.npcs.append(npc)
        self.game_state.party.member_ids.append("npc-tom-123")

        ally = make_combat_participant(
            entity_id="npc-tom-123",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            initiative=20,
        )
        self.game_state.combat.participants = [ally]
        self.game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        # Mock NPC agent that returns suggestion text via process() stream
        mock_agent = Mock()
        suggestion_text = "I'll cast fireball at the goblin"

        async def mock_process(*args: object, **kwargs: Any) -> AsyncIterator[StreamEvent]:
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=suggestion_text),
            )

        mock_agent.process = Mock(return_value=mock_process())
        mock_agent.prepare_for_npc = Mock()
        self.agent_lifecycle.get_npc_agent.return_value = mock_agent

        result = await self.step.run(ctx)

        # Verify agent was retrieved and prepared
        self.agent_lifecycle.get_npc_agent.assert_called_once_with(self.game_state, npc)
        mock_agent.prepare_for_npc.assert_called_once_with(npc)

        # Verify agent.process was called with suggestion prompt
        mock_agent.process.assert_called_once()
        call_args = mock_agent.process.call_args
        assert "It is your turn in combat" in call_args[0][0]
        assert call_args[0][1] == self.game_state
        assert call_args[1]["context"] == ""
        assert call_args[1]["stream"] is False

        # Verify broadcast was called with BroadcastCombatSuggestionCommand
        self.event_bus.submit_and_wait.assert_called_once()
        call_args_list = self.event_bus.submit_and_wait.call_args[0][0]
        assert len(call_args_list) == 1
        broadcast_cmd = call_args_list[0]
        assert broadcast_cmd.npc_id == "npc-tom-123"
        assert broadcast_cmd.npc_name == npc.display_name
        assert broadcast_cmd.action_text == suggestion_text

        # Verify HALT outcome (waiting for player decision)
        assert result.outcome == OrchestrationOutcome.HALT
        assert "Ally NPC" in (result.reason or "")

    @pytest.mark.asyncio
    async def test_uses_default_when_no_suggestion_generated(self) -> None:
        """Test step uses default suggestion when agent returns empty response."""
        npc = make_npc_instance(instance_id="npc-tom-123")
        self.game_state.npcs.append(npc)
        self.game_state.party.member_ids.append("npc-tom-123")

        ally = make_combat_participant(
            entity_id="npc-tom-123",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            initiative=20,
        )
        self.game_state.combat.participants = [ally]
        self.game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=self.game_state)

        # Mock NPC agent that returns empty response
        mock_agent = Mock()

        async def mock_process(*args: object, **kwargs: Any) -> AsyncIterator[StreamEvent]:
            # Simulate empty response - no COMPLETE event
            return
            yield  # Make it an async generator

        mock_agent.process = Mock(return_value=mock_process())
        mock_agent.prepare_for_npc = Mock()
        self.agent_lifecycle.get_npc_agent.return_value = mock_agent

        result = await self.step.run(ctx)

        # Verify default suggestion was broadcast
        call_args_list = self.event_bus.submit_and_wait.call_args[0][0]
        broadcast_cmd = call_args_list[0]
        assert broadcast_cmd.action_text == "I'll attack the nearest enemy."
        assert result.outcome == OrchestrationOutcome.HALT
