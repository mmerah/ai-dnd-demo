"""Tests for WrapAllyActionIfNeeded step."""

import pytest

from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.wrap_ally_action import WrapAllyActionIfNeeded
from tests.factories import (
    make_combat_participant,
    make_combat_state,
    make_game_state,
    make_npc_instance,
    make_npc_sheet,
)


class TestWrapAllyActionIfNeeded:
    """Tests for WrapAllyActionIfNeeded step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.step = WrapAllyActionIfNeeded()

    @pytest.mark.asyncio
    async def test_no_op_when_not_ally_turn(self) -> None:
        """Test no-op when combat not active or not ally turn."""
        # Not in combat
        self.game_state.combat.is_active = False
        ctx = OrchestrationContext(user_message="I attack", game_state=self.game_state)
        result = await self.step.run(ctx)
        assert result.context.user_message == "I attack"

        # Player turn
        combat_state = make_combat_state(is_active=True)
        player = make_combat_participant(
            entity_id="player", entity_type=EntityType.PLAYER, faction=CombatFaction.PLAYER, initiative=15
        )
        combat_state.participants = [player]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state
        ctx = OrchestrationContext(user_message="I attack", game_state=self.game_state)
        result = await self.step.run(ctx)
        assert result.context.user_message == "I attack"

    @pytest.mark.asyncio
    async def test_wraps_message_for_ally_turn(self) -> None:
        """Test wraps message when it's an ally NPC turn."""
        npc_sheet = make_npc_sheet(display_name="Tom", npc_id="npc-tom")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="npc-tom-123")
        self.game_state.npcs.append(npc)
        self.game_state.party.member_ids.append("npc-tom-123")

        combat_state = make_combat_state(is_active=True)
        ally = make_combat_participant(
            entity_id="npc-tom-123", entity_type=EntityType.NPC, name="Tom", faction=CombatFaction.ALLY, initiative=14
        )
        combat_state.participants = [ally]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state

        ctx = OrchestrationContext(user_message="Attack the goblin", game_state=self.game_state)
        result = await self.step.run(ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert "[ALLY_ACTION]" in result.context.user_message
        assert "Tom" in result.context.user_message
        assert "npc-tom-123" in result.context.user_message
        assert "Attack the goblin" in result.context.user_message
        assert "next_turn" in result.context.user_message

    @pytest.mark.asyncio
    async def test_raises_when_ally_not_found(self) -> None:
        """Test raises ValueError when ally NPC not found in game state."""
        combat_state = make_combat_state(is_active=True)
        ally = make_combat_participant(
            entity_id="npc-missing", entity_type=EntityType.NPC, faction=CombatFaction.ALLY, initiative=14
        )
        combat_state.participants = [ally]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state

        ctx = OrchestrationContext(user_message="I attack", game_state=self.game_state)

        with pytest.raises(ValueError, match="Allied NPC npc-missing not found"):
            await self.step.run(ctx)

    @pytest.mark.asyncio
    async def test_raises_when_ally_not_in_party(self) -> None:
        """Test raises ValueError when ally NPC not in party."""
        npc_sheet = make_npc_sheet(display_name="Tom", npc_id="npc-tom")
        npc = make_npc_instance(npc_sheet=npc_sheet, instance_id="npc-tom-123")
        self.game_state.npcs.append(npc)
        # Intentionally not adding to party

        combat_state = make_combat_state(is_active=True)
        ally = make_combat_participant(
            entity_id="npc-tom-123", entity_type=EntityType.NPC, name="Tom", faction=CombatFaction.ALLY, initiative=14
        )
        combat_state.participants = [ally]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state

        ctx = OrchestrationContext(user_message="I attack", game_state=self.game_state)

        with pytest.raises(ValueError, match="Tom.*not in the party"):
            await self.step.run(ctx)
