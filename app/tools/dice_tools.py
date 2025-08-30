"""Dice and combat-related tools for D&D 5e AI Dungeon Master."""

import logging
import re
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastToolCallCommand
from app.events.commands.dice_commands import RollDiceCommand

logger = logging.getLogger(__name__)


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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Extract modifier from dice string if present
    modifier = 0
    dice_pattern = dice
    match = re.match(r"([^+-]+)([+-]\d+)", dice)
    if match:
        dice_pattern = match.group(1)
        modifier = int(match.group(2))

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="roll_dice",
            parameters={"dice": dice, "roll_type": roll_type, "purpose": purpose, "target": target},
        ),
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(
            game_id=game_state.game_id,
            roll_type=roll_type,
            dice=dice_pattern,
            modifier=modifier,
            target=target,
        ),
    )

    # Return the actual result
    if not result:
        raise RuntimeError("Failed to execute dice roll command")

    if not isinstance(result, BaseModel):
        raise TypeError(f"Expected BaseModel from command, got {type(result)}")

    return result
