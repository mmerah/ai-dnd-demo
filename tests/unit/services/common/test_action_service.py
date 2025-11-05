"""Unit tests for ActionService policy enforcement."""

from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest

from app.agents.core.types import AgentType
from app.events.base import BaseCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.game import IEventManager, ISaveManager
from app.models.tool_results import UpdateHPResult
from app.services.common.action_service import ActionService
from tests.factories import make_game_state


class TestActionServicePolicyEnforcement:
    """Test ActionService policy enforcement functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.event_manager = create_autospec(IEventManager, instance=True)
        self.save_manager = create_autospec(ISaveManager, instance=True)

        self.service = ActionService(
            event_bus=self.event_bus,
            event_manager=self.event_manager,
            save_manager=self.save_manager,
        )

        self.game_state = make_game_state()
        self.command = create_autospec(BaseCommand, instance=True)
        self.command.__dict__ = {"game_id": self.game_state.game_id}

    @pytest.mark.asyncio
    async def test_narrative_agent_blocked_during_combat(self) -> None:
        """Test narrative agent cannot use combat tools during active combat."""
        self.game_state.combat.is_active = True

        with pytest.raises(ValueError, match="BLOCKED.*Narrative agent.*roll_dice"):
            await self.service.execute_command_as_action(
                tool_name="roll_dice",
                command=self.command,
                game_state=self.game_state,
                agent_type=AgentType.NARRATIVE,
            )

    @pytest.mark.asyncio
    async def test_combat_agent_allowed_during_combat(self) -> None:
        """Test combat agent can use combat tools during active combat."""
        self.game_state.combat.is_active = True
        result = UpdateHPResult(
            target="goblin",
            old_hp=10,
            new_hp=5,
            max_hp=10,
            amount=-5,
            damage_type="slashing",
            is_healing=False,
            is_unconscious=False,
        )
        self.event_bus.execute_command = AsyncMock(return_value=result)

        actual = await self.service.execute_command_as_action(
            tool_name="update_hp",
            command=self.command,
            game_state=self.game_state,
            agent_type=AgentType.COMBAT,
        )

        assert actual == result
        self.event_bus.submit_and_wait.assert_not_called()

    @pytest.mark.asyncio
    async def test_npc_agent_restricted_tools(self) -> None:
        """Test NPC agent can only use allowed tools."""
        result = MagicMock()
        self.event_bus.execute_command = AsyncMock(return_value=result)

        # Test allowed tool succeeds
        actual = await self.service.execute_command_as_action(
            tool_name="update_location_state",
            command=self.command,
            game_state=self.game_state,
            agent_type=AgentType.NPC,
        )
        assert actual == result

        # Test disallowed tool fails
        with pytest.raises(ValueError, match="BLOCKED.*NPC agent.*update_hp"):
            await self.service.execute_command_as_action(
                tool_name="update_hp",
                command=self.command,
                game_state=self.game_state,
                agent_type=AgentType.NPC,
            )

    @pytest.mark.asyncio
    async def test_player_agent_bypasses_policy(self) -> None:
        """Test that PLAYER agent type bypasses policy checks."""
        self.game_state.combat.is_active = True
        result = MagicMock()
        self.event_bus.execute_command = AsyncMock(return_value=result)

        # Roll dice is blocked for narrative agent during combat
        actual = await self.service.execute_command_as_action(
            tool_name="roll_dice",
            command=self.command,
            game_state=self.game_state,
            agent_type=AgentType.PLAYER,
        )

        assert actual == result
        self.event_bus.submit_and_wait.assert_not_called()
