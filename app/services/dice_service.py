"""Dice rolling service for D&D 5e mechanics."""

import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


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


class DiceService:
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

    def roll_ability_check(
        self,
        ability_modifier: int,
        proficiency_bonus: int = 0,
        dc: int | None = None,
        roll_type: RollType = RollType.NORMAL,
    ) -> dict[str, Any]:
        """
        Roll an ability check with modifiers.

        Args:
            ability_modifier: The ability score modifier
            proficiency_bonus: Proficiency bonus if proficient
            dc: Difficulty class to check against
            roll_type: Advantage/disadvantage

        Returns:
            Dict with roll details and success status
        """
        total_modifier = ability_modifier + proficiency_bonus
        formula = f"1d20{total_modifier:+d}" if total_modifier else "1d20"

        roll = self.roll_dice(formula, roll_type)

        result = {
            "roll": roll,
            "ability_modifier": ability_modifier,
            "proficiency_bonus": proficiency_bonus,
            "total": roll.total,
        }

        if dc is not None:
            result["dc"] = dc
            result["success"] = roll.total >= dc

            # Critical success always succeeds, critical failure always fails
            if roll.is_critical_success:
                result["success"] = True
            elif roll.is_critical_failure:
                result["success"] = False

        return result

    def roll_saving_throw(
        self, ability_modifier: int, proficiency_bonus: int = 0, dc: int = 10, roll_type: RollType = RollType.NORMAL,
    ) -> dict[str, Any]:
        """
        Roll a saving throw.

        Args:
            ability_modifier: The ability score modifier
            proficiency_bonus: Proficiency bonus if proficient
            dc: Difficulty class to beat
            roll_type: Advantage/disadvantage

        Returns:
            Dict with roll details and success status
        """
        return self.roll_ability_check(
            ability_modifier=ability_modifier, proficiency_bonus=proficiency_bonus, dc=dc, roll_type=roll_type,
        )

    def roll_attack(self, attack_bonus: int, target_ac: int, roll_type: RollType = RollType.NORMAL) -> dict[str, Any]:
        """
        Roll an attack against a target's AC.

        Args:
            attack_bonus: Total attack bonus
            target_ac: Target's armor class
            roll_type: Advantage/disadvantage

        Returns:
            Dict with roll details, hit status, and critical status
        """
        formula = f"1d20{attack_bonus:+d}" if attack_bonus else "1d20"
        roll = self.roll_dice(formula, roll_type)

        # Natural 20 always hits, natural 1 always misses
        if roll.is_critical_success:
            hit = True
            is_critical_hit = True
        elif roll.is_critical_failure:
            hit = False
            is_critical_hit = False
        else:
            hit = roll.total >= target_ac
            is_critical_hit = False

        return {
            "roll": roll,
            "attack_bonus": attack_bonus,
            "target_ac": target_ac,
            "hit": hit,
            "is_critical_hit": is_critical_hit,
            "total": roll.total,
        }

    def roll_damage(self, damage_formula: str, is_critical: bool = False) -> DiceRoll:
        """
        Roll damage dice.

        Args:
            damage_formula: Damage dice formula (e.g., "1d8+3")
            is_critical: If True, double the dice count

        Returns:
            DiceRoll result
        """
        if is_critical:
            # Parse and double the dice count for critical hits
            dice_count, dice_sides, modifier = self.parse_dice_formula(damage_formula)
            formula = f"{dice_count * 2}d{dice_sides}{modifier:+d}" if modifier else f"{dice_count * 2}d{dice_sides}"
        else:
            formula = damage_formula

        return self.roll_dice(formula)

    def roll_initiative(self, dexterity_modifier: int) -> int:
        """
        Roll initiative for combat.

        Args:
            dexterity_modifier: Character's dexterity modifier

        Returns:
            Initiative total
        """
        formula = f"1d20{dexterity_modifier:+d}" if dexterity_modifier else "1d20"
        roll = self.roll_dice(formula)
        return roll.total
