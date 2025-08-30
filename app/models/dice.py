"""Dice rolling models for D&D 5e mechanics."""

from dataclasses import dataclass
from enum import Enum


class RollType(Enum):
    """Types of dice roll mechanics."""

    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


@dataclass
class DiceRoll:
    """Represents a single dice roll result."""

    dice_count: int
    dice_sides: int
    modifier: int
    rolls: list[int]
    total: int
    is_critical_success: bool = False
    is_critical_failure: bool = False
    roll_type: RollType = RollType.NORMAL

    @property
    def formula(self) -> str:
        """Return the dice formula string."""
        base = f"{self.dice_count}d{self.dice_sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        if self.modifier < 0:
            return f"{base}{self.modifier}"
        return base
