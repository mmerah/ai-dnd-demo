"""Character management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.events.commands.broadcast_commands import BroadcastToolCallCommand
from app.events.commands.character_commands import (
    AddConditionCommand,
    RemoveConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.models.dependencies import AgentDependencies

logger = logging.getLogger(__name__)


async def update_hp(
    ctx: RunContext[AgentDependencies], amount: int, damage_type: str = "untyped", target: str = "player"
) -> dict[str, Any]:
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="update_hp",
            parameters={"amount": amount, "damage_type": damage_type, "target": target},
        )
    )

    # Execute the HP update and get the result
    result = await event_bus.execute_command(
        UpdateHPCommand(game_id=game_state.game_id, target=target, amount=amount, damage_type=damage_type)
    )

    # Return the actual result
    if result:
        return result
    else:
        # Fallback return if no result data
        return {
            "type": "hp_update",
            "target": target,
            "amount": amount,
            "damage_type": damage_type,
        }


async def add_condition(
    ctx: RunContext[AgentDependencies], condition: str, duration: int = 0, target: str = "player"
) -> dict[str, Any]:
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="add_condition",
            parameters={"condition": condition, "duration": duration, "target": target},
        )
    )

    # Execute the add condition command and get the result
    result = await event_bus.execute_command(
        AddConditionCommand(game_id=game_state.game_id, target=target, condition=condition, duration=duration)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {
            "type": "add_condition",
            "target": target,
            "condition": condition,
            "duration": duration,
        }


async def remove_condition(
    ctx: RunContext[AgentDependencies], condition: str, target: str = "player"
) -> dict[str, Any]:
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="remove_condition",
            parameters={"condition": condition, "target": target},
        )
    )

    # Execute the remove condition command and get the result
    result = await event_bus.execute_command(
        RemoveConditionCommand(game_id=game_state.game_id, target=target, condition=condition)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "remove_condition", "target": target, "condition": condition}


async def update_spell_slots(ctx: RunContext[AgentDependencies], level: int, amount: int) -> dict[str, Any]:
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id, tool_name="update_spell_slots", parameters={"level": level, "amount": amount}
        )
    )

    # Execute the update spell slots command and get the result
    result = await event_bus.execute_command(
        UpdateSpellSlotsCommand(game_id=game_state.game_id, level=level, amount=amount)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "spell_slots_update", "level": level, "amount": amount}
