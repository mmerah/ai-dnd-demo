"""Unit tests for DiceHandler."""

from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.events.commands.dice_commands import RollDiceCommand
from app.events.handlers.dice_handler import DiceHandler
from app.interfaces.services.common import IDiceService
from app.models.dice import DiceRoll, RollType
from app.models.tool_results import RollDiceResult
from tests.factories import make_game_state


class TestDiceHandler:
    """Test DiceHandler command processing."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.dice_service = create_autospec(IDiceService, instance=True)
        self.handler = DiceHandler(self.dice_service)
        self.game_state = make_game_state()

    @pytest.mark.asyncio
    async def test_roll_dice_basic(self) -> None:
        """Test basic dice roll."""
        dice_result = DiceRoll(
            dice_count=1,
            dice_sides=20,
            modifier=0,
            rolls=[15],
            total=15,
            is_critical_success=False,
            is_critical_failure=False,
        )
        base_notation = "1d20"
        self.dice_service.parse_special_notation.return_value = (base_notation, RollType.NORMAL)
        self.dice_service.roll_dice.return_value = dice_result

        command = RollDiceCommand(
            game_id=self.game_state.game_id,
            dice="1d20",
            modifier=0,
            roll_type="ability",
            ability="STR",
            agent_type=AgentType.NARRATIVE,
        )

        result = await self.handler.handle(command, self.game_state)

        assert not result.mutated
        assert isinstance(result.data, RollDiceResult)
        assert result.data.rolls == dice_result.rolls
        assert result.data.total == dice_result.total

    @pytest.mark.asyncio
    async def test_roll_dice_with_modifier(self) -> None:
        """Test dice roll with modifier."""
        dice_result = DiceRoll(
            dice_count=1,
            dice_sides=20,
            modifier=5,
            rolls=[12],
            total=17,
            is_critical_success=False,
            is_critical_failure=False,
        )
        base_notation = "1d20"
        self.dice_service.parse_special_notation.return_value = (base_notation, RollType.NORMAL)
        self.dice_service.roll_dice.return_value = dice_result

        command = RollDiceCommand(
            game_id=self.game_state.game_id,
            dice=base_notation,
            modifier=5,
            roll_type="attack",
            agent_type=AgentType.COMBAT,
        )

        result = await self.handler.handle(command, self.game_state)

        assert isinstance(result.data, RollDiceResult)
        assert result.data.total == dice_result.total
        expected_notation = f"{base_notation}+{command.modifier}"
        self.dice_service.roll_dice.assert_called_once_with(expected_notation, RollType.NORMAL)

    @pytest.mark.asyncio
    async def test_roll_dice_critical_success(self) -> None:
        """Test critical success detection."""
        dice_result = DiceRoll(
            dice_count=1,
            dice_sides=20,
            modifier=0,
            rolls=[20],
            total=20,
            is_critical_success=True,
            is_critical_failure=False,
        )
        self.dice_service.parse_special_notation.return_value = ("1d20", RollType.NORMAL)
        self.dice_service.roll_dice.return_value = dice_result

        command = RollDiceCommand(
            game_id=self.game_state.game_id,
            dice="1d20",
            modifier=0,
            roll_type="attack",
            agent_type=AgentType.COMBAT,
        )

        result = await self.handler.handle(command, self.game_state)

        assert isinstance(result.data, RollDiceResult)
        assert result.data.critical
        assert result.data.rolls == dice_result.rolls

    @pytest.mark.asyncio
    async def test_combat_roll_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for non-combat agent during combat."""
        self.game_state.combat.is_active = True

        dice_result = DiceRoll(
            dice_count=1,
            dice_sides=20,
            modifier=0,
            rolls=[10],
            total=10,
            is_critical_success=False,
            is_critical_failure=False,
        )
        self.dice_service.parse_special_notation.return_value = ("1d20", RollType.NORMAL)
        self.dice_service.roll_dice.return_value = dice_result

        command = RollDiceCommand(
            game_id=self.game_state.game_id,
            dice="1d20",
            modifier=0,
            roll_type="attack",
            agent_type=AgentType.NARRATIVE,
        )

        await self.handler.handle(command, self.game_state)

        assert "should be COMBAT agent only" in caplog.text
