"""Dice and combat-related tools for D&D 5e AI Dungeon Master."""

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
    if kwargs.get("target") is not None:
        command_kwargs["target"] = kwargs.get("target")
    if kwargs.get("apply_to_entity_id") is not None:
        command_kwargs["apply_to_entity_id"] = kwargs.get("apply_to_entity_id")
    if kwargs.get("apply_as_damage") is not None:
        command_kwargs["apply_as_damage"] = kwargs.get("apply_as_damage")
    if kwargs.get("apply_to_entity_type") is not None:
        command_kwargs["apply_to_entity_type"] = kwargs.get("apply_to_entity_type")

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
    target: str | None = None,
    apply_to_entity_id: str | None = None,
    apply_as_damage: bool = False,
    apply_to_entity_type: Literal["player", "npc", "monster"] | None = None,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Roll dice for any purpose in D&D 5e.

    Args:
        dice: The dice to roll (e.g., "1d20", "2d6", "2d20kh" for advantage)
        modifier: The numerical modifier to add to the roll (can be 0 or negative)
        roll_type: The category of roll ('ability_check', 'saving_throw', 'attack', 'damage', 'initiative')
        purpose: A human-readable description of the roll (e.g., "Stealth Check", "Longsword Damage")
        target: The name of the character or NPC being targeted or making the roll
        apply_to_entity_id: If roll_type is 'damage' and this is set, automatically apply damage to this entity
        apply_as_damage: If True and roll_type is 'damage', automatically apply the rolled damage

    Examples:
        - Stealth check: dice="1d20", modifier=5, roll_type="ability_check", purpose="Stealth Check"
        - Constitution save: dice="1d20", modifier=2, roll_type="saving_throw", purpose="Poison Save"
        - Longsword attack: dice="1d20", modifier=7, roll_type="attack", purpose="Longsword Attack", target="Goblin"
        - Damage roll: dice="1d8", modifier=4, roll_type="damage", purpose="Longsword Damage"
        - Auto-apply damage: dice="1d8", modifier=4, roll_type="damage", purpose="Longsword Damage", apply_to_entity_id="goblin-1", apply_to_entity_type="monster", apply_as_damage=True
        - Initiative: dice="1d20", modifier=3, roll_type="initiative", purpose="Combat Initiative"
        - Advantage roll: dice="2d20kh", modifier=5, roll_type="ability_check", purpose="Perception with Advantage"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
