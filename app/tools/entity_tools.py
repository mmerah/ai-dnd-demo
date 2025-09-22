"""Entity management tools for D&D 5e AI Dungeon Master.

IMPORTANT: During active combat, update_hp and update_condition should ONLY be used by the combat agent.
The narrative agent uses these for non-combat situations only.
"""

import logging
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.entity_commands import (
    LevelUpCommand,
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.models.attributes import EntityType
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

    **IMPORTANT**: During active combat, this tool should ONLY be used by the COMBAT AGENT.
    The narrative agent can use this for non-combat healing/damage only.

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

    **IMPORTANT**: During active combat, this tool should ONLY be used by the COMBAT AGENT.
    The narrative agent can use this for non-combat conditions only.

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
async def update_spell_slots(
    ctx: RunContext[AgentDependencies], entity_id: str, entity_type: EntityType, level: int, amount: int
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Update spell slots for an entity.

    Use when spells are cast or slots are restored.

    Args:
        entity_id: Instance ID of target
        entity_type: One of 'player' | 'npc' | 'monster'
        level: Spell level (1-9)
        amount: Change in slots (negative to use, positive to restore)

    Examples:
        - Cast level 1 spell (player): entity_type="player", entity_id="<player-id>", level=1, amount=-1
        - Restore level 2 slot (NPC): entity_type="npc", entity_id="<npc-id>", level=2, amount=1
        - NPC casts fireball: entity_type="npc", entity_id="<npc-id>", level=3, amount=-1
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(LevelUpCommand)
async def level_up(ctx: RunContext[AgentDependencies], entity_id: str, entity_type: EntityType) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Level up an entity by one level.

    Use when an entity has earned enough XP or for testing progression.

    Args:
        entity_id: Instance ID of target
        entity_type: One of 'player' | 'npc' | 'monster'

    Examples:
        - Level up player: entity_type="player", entity_id="<player-id>"
        - Level up NPC: entity_type="npc", entity_id="<npc-id>"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
