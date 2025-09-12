"""Dice rolling tools for D&D 5e AI Dungeon Master.

IMPORTANT: During active combat, dice rolls should ONLY be made by the combat agent.
The narrative agent uses this for non-combat rolls only.
"""

import logging
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

    - Pass dice and modifier directly to the command (no extraction needed).
    - Remove non-command fields like "purpose" from command kwargs.
    - Keep original kwargs for broadcasting to frontend.
    """
    original: dict[str, JSONSerializable] = cast(dict[str, JSONSerializable], dict(kwargs))

    command_kwargs: dict[str, Any] = {
        "roll_type": kwargs.get("roll_type"),
        "dice": kwargs.get("dice", "").strip(),
        "modifier": kwargs.get("modifier", 0),
    }
    if kwargs.get("ability") is not None:
        command_kwargs["ability"] = kwargs.get("ability")
    if kwargs.get("skill") is not None:
        command_kwargs["skill"] = kwargs.get("skill")

    # Broadcast original inputs including purpose for UX clarity
    broadcast_kwargs: dict[str, JSONSerializable] = original

    return command_kwargs, broadcast_kwargs


@tool_handler(RollDiceCommand, prepare=_prepare_roll_command_kwargs)
async def roll_dice(
    ctx: RunContext[AgentDependencies],
    dice: str,
    modifier: int,
    roll_type: Literal["ability_check", "saving_throw", "attack", "damage", "initiative"],
    purpose: str,
    ability: str | None = None,
    skill: str | None = None,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Roll dice for any purpose in D&D 5e.

    **IMPORTANT**: During active combat, this tool should ONLY be used by the COMBAT AGENT.
    The narrative agent should NOT use this for combat rolls (attack, damage, initiative).

    **IMPORTANT**: After rolling damage, you MUST use the update_hp tool to apply the damage to the target!

    Args:
        dice: The dice to roll (e.g., "1d20", "2d6", "2d20kh" for advantage)
        modifier: The numerical modifier to add to the roll (can be 0 or negative)
        roll_type: The category of roll ('ability_check', 'saving_throw', 'attack', 'damage', 'initiative')
        purpose: A human-readable description of the roll (e.g., "Stealth Check", "Longsword Damage")
        ability: The ability being used (optional, e.g., "Strength", "Dexterity")
        skill: The skill being used (optional, e.g., "Stealth", "Athletics")

    Examples:
        - Stealth check: dice="1d20", modifier=5, roll_type="ability_check", purpose="Stealth Check", ability="Dexterity", skill="Stealth"
        - Constitution save: dice="1d20", modifier=2, roll_type="saving_throw", purpose="Poison Save", ability="Constitution"
        - Longsword attack: dice="1d20", modifier=7, roll_type="attack", purpose="Longsword Attack"
        - Damage roll: dice="1d8", modifier=4, roll_type="damage", purpose="Longsword Damage"
          Then call: update_hp(entity_id="goblin-1", entity_type="monster", amount=-8, damage_type="slashing")
        - Initiative: dice="1d20", modifier=3, roll_type="initiative", purpose="Combat Initiative"
        - Advantage roll: dice="2d20kh", modifier=5, roll_type="ability_check", purpose="Perception with Advantage", ability="Wisdom", skill="Perception"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
