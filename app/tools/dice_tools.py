"""Dice and combat-related tools for D&D 5e AI Dungeon Master."""

import logging
import re
from typing import Any, Literal, cast

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.common.types import JSONSerializable
from app.events.commands.dice_commands import RollDiceCommand
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


def _prepare_roll_command_kwargs(
    kwargs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, JSONSerializable]]:
    """Transform dice tool kwargs into command kwargs and broadcast kwargs.

    - Extract numeric modifier from the dice formula (e.g., "1d20+5" → modifier=+5, dice="1d20").
    - Remove non-command fields like "purpose" from command kwargs.
    - Keep original kwargs for broadcasting to frontend.
    """
    original: dict[str, JSONSerializable] = cast(dict[str, JSONSerializable], dict(kwargs))

    dice_str = str(kwargs.get("dice", "")).strip()
    modifier = 0
    dice_pattern = dice_str

    # Extract trailing +N / -N modifier if present
    match = re.match(r"^([^+-]+)([+-]\d+)$", dice_str)
    if match:
        dice_pattern = match.group(1)
        try:
            modifier = int(match.group(2))
        except ValueError:
            modifier = 0

    command_kwargs: dict[str, Any] = {
        "roll_type": kwargs.get("roll_type"),
        "dice": dice_pattern,
        "modifier": modifier,
    }
    if kwargs.get("target") is not None:
        command_kwargs["target"] = kwargs.get("target")

    # Broadcast original inputs including purpose for UX clarity
    broadcast_kwargs: dict[str, JSONSerializable] = original

    return command_kwargs, broadcast_kwargs


@tool_handler(RollDiceCommand, prepare=_prepare_roll_command_kwargs)
async def roll_dice(
    ctx: RunContext[AgentDependencies],
    dice: str,
    roll_type: Literal["ability_check", "saving_throw", "attack", "damage", "initiative"],
    purpose: str,
    target: str | None = None,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Roll dice for any purpose in D&D 5e.

    The AI is responsible for constructing the full dice formula, including modifiers.

    Args:
        dice: The dice formula (e.g., "1d20+5", "2d6+3", "2d20kh" for advantage)
        roll_type: The category of roll ('ability_check', 'saving_throw', 'attack', 'damage', 'initiative')
        purpose: A human-readable description of the roll (e.g., "Stealth Check", "Longsword Damage")
        target: The name of the character or NPC being targeted or making the roll

    Examples:
        - Stealth check: dice="1d20+5", roll_type="ability_check", purpose="Stealth Check"
        - Constitution save: dice="1d20+2", roll_type="saving_throw", purpose="Poison Save"
        - Longsword attack: dice="1d20+7", roll_type="attack", purpose="Longsword Attack", target="Goblin"
        - Damage roll: dice="1d8+4", roll_type="damage", purpose="Longsword Damage"
        - Initiative: dice="1d20+3", roll_type="initiative", purpose="Combat Initiative"
        - Advantage roll: dice="2d20kh+5", roll_type="ability_check", purpose="Perception with Advantage"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
