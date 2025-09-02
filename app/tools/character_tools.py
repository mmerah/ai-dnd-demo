"""Character management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.character_commands import (
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(UpdateHPCommand)
async def update_hp(
    ctx: RunContext[AgentDependencies],
    amount: int,
    damage_type: str = "untyped",
    target: str = "player",
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Update hit points for damage or healing.

    Use after damage rolls or healing effects.

    Args:
        amount: HP change (negative for damage, positive for healing)
        damage_type: Type of damage/healing
        target: 'player' or NPC name

    Examples:
        - Deal 7 damage: amount=-7, damage_type="slashing"
        - Heal 5 HP: amount=5, damage_type="healing"
        - Poison damage to NPC: amount=-3, damage_type="poison", target="Goblin"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(UpdateConditionCommand)
async def update_condition(
    ctx: RunContext[AgentDependencies],
    target: str,
    condition: str,
    action: Literal["add", "remove"],
    duration: int = 0,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove a status condition from a target.

    Args:
        target: 'player' or the name of an NPC
        condition: The condition to apply or remove (e.g., 'poisoned', 'prone', 'frightened')
        action: Whether to 'add' or 'remove' the condition
        duration: Duration in rounds (0 for until removed) - only used when adding

    Examples:
        - Apply poison: target="player", condition="poisoned", action="add", duration=3
        - Remove poison: target="player", condition="poisoned", action="remove"
        - Knock prone: target="Goblin", condition="prone", action="add"
        - Stand up: target="player", condition="prone", action="remove"
        - Fear spell: target="Orc", condition="frightened", action="add", duration=2
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(UpdateSpellSlotsCommand)
async def update_spell_slots(ctx: RunContext[AgentDependencies], level: int, amount: int) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Update spell slots for the player.

    Use when spells are cast or slots are restored.

    Args:
        level: Spell level (1-9)
        amount: Change in slots (negative to use, positive to restore)

    Examples:
        - Cast level 1 spell: level=1, amount=-1
        - Restore level 2 slot: level=2, amount=1
        - Cast Hunter's Mark: level=1, amount=-1
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
