"""Utility functions for ability score mappings and conversions."""

from enum import Enum
from typing import Literal

from app.models.attributes import Abilities, AbilityModifiers


class AbilityType(str, Enum):
    """Standard D&D 5e ability types."""

    STRENGTH = "STR"
    DEXTERITY = "DEX"
    CONSTITUTION = "CON"
    INTELLIGENCE = "INT"
    WISDOM = "WIS"
    CHARISMA = "CHA"


AbilityName = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
AbilityCode = Literal["STR", "DEX", "CON", "INT", "WIS", "CHA"]

ABILITY_NAME_TO_CODE: dict[AbilityName, AbilityCode] = {
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA",
}

ABILITY_CODE_TO_NAME: dict[AbilityCode, AbilityName] = {
    "STR": "strength",
    "DEX": "dexterity",
    "CON": "constitution",
    "INT": "intelligence",
    "WIS": "wisdom",
    "CHA": "charisma",
}

ALL_ABILITY_CODES: list[AbilityCode] = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


def normalize_ability_name(ability: str) -> AbilityCode | None:
    """Convert any ability name format to standard code (STR, DEX, etc.).

    Args:
        ability: Ability name in any format (e.g., "strength", "Strength", "STR", "str")

    Returns:
        Standard ability code or None if not recognized
    """
    ability_lower = ability.lower()

    # Check if it's already a code (uppercase it)
    if ability_lower in ("str", "dex", "con", "int", "wis", "cha"):
        return ability.upper()  # type: ignore[return-value]

    # Check if it's a full name
    if ability_lower in ABILITY_NAME_TO_CODE:
        return ABILITY_NAME_TO_CODE[ability_lower]  # type: ignore[index]

    return None


def get_ability_modifier(abilities: Abilities | AbilityModifiers, ability_code: AbilityCode) -> int:
    """Get the value for a specific ability from Abilities or AbilityModifiers.

    Args:
        abilities: Abilities or AbilityModifiers object
        ability_code: Standard ability code (STR, DEX, etc.)

    Returns:
        The ability score or modifier value
    """
    value = getattr(abilities, ability_code)
    assert isinstance(value, int), f"Expected int for ability {ability_code}, got {type(value)}"
    return value


def set_ability_value(abilities: Abilities | AbilityModifiers | object, ability_code: AbilityCode, value: int) -> None:
    """Set the value for a specific ability.

    Args:
        abilities: Object with ability attributes
        ability_code: Standard ability code (STR, DEX, etc.)
        value: Value to set
    """
    setattr(abilities, ability_code, value)
