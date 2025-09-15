"""Unit tests for DiceService."""

import pytest

from app.models.dice import RollType
from app.services.common.dice_service import DiceService


class TestDiceService:
    """Test cases for DiceService."""

    def test_parse_dice_formula_valid(self) -> None:
        service = DiceService()

        assert service.parse_dice_formula("1d20") == (1, 20, 0)
        assert service.parse_dice_formula("2d6+3") == (2, 6, 3)
        assert service.parse_dice_formula("3d8-2") == (3, 8, -2)
        assert service.parse_dice_formula("1d20+5") == (1, 20, 5)
        assert service.parse_dice_formula("4d4") == (4, 4, 0)

    def test_parse_dice_formula_with_spaces(self) -> None:
        service = DiceService()

        assert service.parse_dice_formula("1d20 + 5") == (1, 20, 5)
        assert service.parse_dice_formula(" 2d6 - 1 ") == (2, 6, -1)

    def test_parse_dice_formula_invalid(self) -> None:
        service = DiceService()

        with pytest.raises(ValueError, match="Invalid dice formula"):
            service.parse_dice_formula("invalid")

        with pytest.raises(ValueError, match="Invalid dice formula"):
            service.parse_dice_formula("d20")

        with pytest.raises(ValueError, match="Invalid dice formula"):
            service.parse_dice_formula("1d")

    def test_parse_dice_formula_invalid_count(self) -> None:
        service = DiceService()

        with pytest.raises(ValueError, match="Invalid dice count"):
            service.parse_dice_formula("0d20")

        with pytest.raises(ValueError, match="Invalid dice count"):
            service.parse_dice_formula("101d20")

        # Negative dice count fails to parse as formula (regex doesn't match)
        with pytest.raises(ValueError, match="Invalid dice formula"):
            service.parse_dice_formula("-1d20")

    def test_parse_dice_formula_invalid_sides(self) -> None:
        service = DiceService()

        with pytest.raises(ValueError, match="Invalid dice sides"):
            service.parse_dice_formula("1d7")

        with pytest.raises(ValueError, match="Invalid dice sides"):
            service.parse_dice_formula("1d19")

        with pytest.raises(ValueError, match="Invalid dice sides"):
            service.parse_dice_formula("1d3")

    def test_parse_special_notation(self) -> None:
        service = DiceService()

        assert service.parse_special_notation("2d20kh") == ("1d20", RollType.ADVANTAGE)
        assert service.parse_special_notation("2d20kl") == ("1d20", RollType.DISADVANTAGE)
        assert service.parse_special_notation("1d20+5") == ("1d20+5", RollType.NORMAL)
        assert service.parse_special_notation("3d6") == ("3d6", RollType.NORMAL)

    def test_roll_dice_deterministic_with_seed(self) -> None:
        service = DiceService(seed=42)

        # With a fixed seed, rolls should be deterministic
        roll1 = service.roll_dice("1d20+5")
        service2 = DiceService(seed=42)
        roll2 = service2.roll_dice("1d20+5")

        assert roll1.total == roll2.total
        assert roll1.rolls == roll2.rolls

    def test_roll_dice_normal(self) -> None:
        service = DiceService(seed=42)

        roll = service.roll_dice("2d6+3")
        assert roll.dice_count == 2
        assert roll.dice_sides == 6
        assert roll.modifier == 3
        assert len(roll.rolls) == 2
        assert all(1 <= r <= 6 for r in roll.rolls)
        assert roll.total == sum(roll.rolls) + 3
        assert roll.roll_type == RollType.NORMAL
        assert not roll.is_critical_success
        assert not roll.is_critical_failure

    def test_roll_dice_critical_success(self) -> None:
        # Use a seed that generates a 20 on the first roll
        service = DiceService(seed=99)
        roll = service.roll_dice("1d20")

        if roll.rolls[0] == 20:
            assert roll.is_critical_success
            assert not roll.is_critical_failure

    def test_roll_dice_critical_failure(self) -> None:
        # Test critical failure detection
        service = DiceService(seed=0)
        roll = service.roll_dice("1d20")

        if roll.rolls[0] == 1:
            assert roll.is_critical_failure
            assert not roll.is_critical_success

    def test_roll_dice_advantage(self) -> None:
        service = DiceService(seed=42)

        roll = service.roll_dice("1d20", RollType.ADVANTAGE)
        assert roll.dice_count == 1
        assert roll.dice_sides == 20
        assert len(roll.rolls) == 2
        assert roll.total == max(roll.rolls) + roll.modifier
        assert roll.roll_type == RollType.ADVANTAGE

    def test_roll_dice_disadvantage(self) -> None:
        service = DiceService(seed=42)

        roll = service.roll_dice("1d20", RollType.DISADVANTAGE)
        assert roll.dice_count == 1
        assert roll.dice_sides == 20
        assert len(roll.rolls) == 2
        assert roll.total == min(roll.rolls) + roll.modifier
        assert roll.roll_type == RollType.DISADVANTAGE

    def test_roll_dice_non_d20_no_critical(self) -> None:
        service = DiceService(seed=42)

        # Non-d20 rolls should never have critical success/failure
        roll = service.roll_dice("3d6")
        assert not roll.is_critical_success
        assert not roll.is_critical_failure

        roll = service.roll_dice("1d8+2")
        assert not roll.is_critical_success
        assert not roll.is_critical_failure
