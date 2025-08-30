"""Character management tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.character_commands import (
    AddConditionCommand,
    RemoveConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(UpdateHPCommand)
async def update_hp(
    ctx: RunContext[AgentDependencies], amount: int, damage_type: str = "untyped", target: str = "player",
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


@tool_handler(AddConditionCommand)
async def add_condition(
    ctx: RunContext[AgentDependencies], condition: str, duration: int = 0, target: str = "player",
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add a status condition to a character.

    Use when effects impose conditions.

    Args:
        condition: Name of condition (poisoned, frightened, prone, etc.)
        duration: Duration in rounds (0 for until removed)
        target: 'player' or NPC name

    Examples:
        - Poison effect: condition="poisoned", duration=3
        - Knocked prone: condition="prone", duration=0
        - Fear spell on NPC: condition="frightened", duration=2, target="Goblin"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(RemoveConditionCommand)
async def remove_condition(
    ctx: RunContext[AgentDependencies], condition: str, target: str = "player",
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Remove a condition from a character.

    Use when conditions end or are cured.

    Args:
        condition: Name of condition to remove
        target: 'player' or NPC name

    Examples:
        - Remove poison: condition="poisoned"
        - Stand up: condition="prone"
        - End fear on NPC: condition="frightened", target="Goblin"
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
