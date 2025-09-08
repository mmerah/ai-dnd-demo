"""Dice rolling service for D&D 5e mechanics."""

import random
import re

from app.interfaces.services.common import IDiceService
from app.models.dice import DiceRoll, RollType


class DiceService(IDiceService):
    """Service for handling all dice rolling mechanics."""

    DICE_PATTERN = re.compile(r"(\d+)d(\d+)([+-]\d+)?")

    def __init__(self, seed: int | None = None):
        """Initialize the dice service with optional seed for testing."""
        if seed is not None:
            random.seed(seed)

    def parse_dice_formula(self, formula: str) -> tuple[int, int, int]:
        """
        Parse a dice formula string (e.g., "2d6+3") into components.

        Args:
            formula: Dice formula string in XdY+Z format

        Returns:
            Tuple of (dice_count, dice_sides, modifier)

        Raises:
            ValueError: If formula is invalid
        """
        formula = formula.replace(" ", "")
        match = self.DICE_PATTERN.match(formula)

        if not match:
            raise ValueError(f"Invalid dice formula: {formula}")

        dice_count = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3) or 0)

        if dice_count < 1 or dice_count > 100:
            raise ValueError(f"Invalid dice count: {dice_count}")
        if dice_sides not in [4, 6, 8, 10, 12, 20, 100]:
            raise ValueError(f"Invalid dice sides: {dice_sides}")

        return dice_count, dice_sides, modifier

    def roll_dice(self, formula: str, roll_type: RollType = RollType.NORMAL) -> DiceRoll:
        """
        Roll dice based on formula with optional advantage/disadvantage.

        Args:
            formula: Dice formula (e.g., "1d20+5")
            roll_type: Type of roll (normal, advantage, disadvantage)

        Returns:
            DiceRoll result object
        """
        dice_count, dice_sides, modifier = self.parse_dice_formula(formula)

        # For d20 rolls with advantage/disadvantage
        if dice_sides == 20 and dice_count == 1 and roll_type != RollType.NORMAL:
            rolls = [random.randint(1, dice_sides), random.randint(1, dice_sides)]
            selected_roll = max(rolls) if roll_type == RollType.ADVANTAGE else min(rolls)

            total = selected_roll + modifier
            is_critical_success = selected_roll == 20
            is_critical_failure = selected_roll == 1

            return DiceRoll(
                dice_count=dice_count,
                dice_sides=dice_sides,
                modifier=modifier,
                rolls=rolls,
                total=total,
                is_critical_success=is_critical_success,
                is_critical_failure=is_critical_failure,
                roll_type=roll_type,
            )

        # Normal rolls
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
        total = sum(rolls) + modifier

        # Critical detection only for d20 rolls
        is_critical_success = dice_sides == 20 and dice_count == 1 and rolls[0] == 20
        is_critical_failure = dice_sides == 20 and dice_count == 1 and rolls[0] == 1

        return DiceRoll(
            dice_count=dice_count,
            dice_sides=dice_sides,
            modifier=modifier,
            rolls=rolls,
            total=total,
            is_critical_success=is_critical_success,
            is_critical_failure=is_critical_failure,
            roll_type=roll_type,
        )
