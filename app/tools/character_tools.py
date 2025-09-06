"""Character management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.character_commands import (
    LevelUpCommand,
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.models.entity import EntityType
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(UpdateHPCommand)
async def update_hp(
    ctx: RunContext[AgentDependencies],
    entity_id: str,
    entity_type: EntityType,
    amount: int,
    damage_type: str = "untyped",
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Update hit points for damage or healing.

    Use after damage rolls or healing effects.

    Args:
        entity_id: Instance ID of target
        entity_type: One of 'player' | 'npc' | 'monster'
        amount: HP change (negative for damage, positive for healing)
        damage_type: Type of damage/healing

    Examples:
        - Deal 7 damage to monster: entity_type="monster", entity_id="<id>", amount=-7, damage_type="slashing"
        - Heal 5 HP (player): entity_type="player", entity_id="<player-id>", amount=5
        - Poison damage to NPC: entity_type="npc", entity_id="<npc-id>", amount=-3, damage_type="poison"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(UpdateConditionCommand)
async def update_condition(
    ctx: RunContext[AgentDependencies],
    entity_id: str,
    entity_type: EntityType,
    condition: str,
    action: Literal["add", "remove"],
    duration: int = 0,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove a status condition from a target.

    Args:
        entity_id: Instance ID of target (player, npc, or monster)
        entity_type: One of 'player' | 'npc' | 'monster'
        condition: The condition to apply or remove (e.g., 'poisoned', 'prone', 'frightened')
        action: Whether to 'add' or 'remove' the condition
        duration: Duration in rounds (0 for until removed) - only used when adding

    Examples:
        - Apply poison to monster: entity_type="monster", entity_id="<id>", condition="poisoned", action="add", duration=3
        - Remove poison from player: entity_type="player", entity_id="<player-id>", condition="poisoned", action="remove"
        - Knock NPC prone: entity_type="npc", entity_id="<npc-id>", condition="prone", action="add"
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


@tool_handler(LevelUpCommand)
async def level_up(ctx: RunContext[AgentDependencies]) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Level up the player character by one level.

    Use when the player has earned enough XP or for testing progression.
    No parameters; applies to the player character.
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
