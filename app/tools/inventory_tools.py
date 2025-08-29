"""Inventory management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastToolCallCommand
from app.events.commands.inventory_commands import (
    AddItemCommand,
    ModifyCurrencyCommand,
    RemoveItemCommand,
)

logger = logging.getLogger(__name__)


async def modify_currency(
    ctx: RunContext[AgentDependencies], gold: int = 0, silver: int = 0, copper: int = 0
) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Modify the player's currency.

    Use when the player gains or spends money.

    Args:
        gold: Gold pieces to add (negative to remove)
        silver: Silver pieces to add (negative to remove)
        copper: Copper pieces to add (negative to remove)

    Examples:
        - Find treasure: gold=5, silver=10
        - Buy item: gold=-3
        - Tavern tip: silver=-5, copper=-2
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="modify_currency",
            parameters={"gold": gold, "silver": silver, "copper": copper},
        )
    )

    # Execute the modify currency command and get the result
    result = await event_bus.execute_command(
        ModifyCurrencyCommand(game_id=game_state.game_id, gold=gold, silver=silver, copper=copper)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "currency_update", "gold": gold, "silver": silver, "copper": copper}


async def add_item(ctx: RunContext[AgentDependencies], item_name: str, quantity: int = 1) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Add an item to the player's inventory.

    Use when the player acquires items.

    Args:
        item_name: Name of the item
        quantity: Number to add

    Examples:
        - Find potion: item_name="Healing Potion"
        - Buy rope: item_name="Rope (50 ft)"
        - Loot arrows: item_name="Arrows", quantity=20
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id, tool_name="add_item", parameters={"item_name": item_name, "quantity": quantity}
        )
    )

    # Execute the add item command and get the result
    result = await event_bus.execute_command(
        AddItemCommand(game_id=game_state.game_id, item_name=item_name, quantity=quantity)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "add_item", "item": item_name, "quantity": quantity}


async def remove_item(ctx: RunContext[AgentDependencies], item_name: str, quantity: int = 1) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Remove an item from the player's inventory.

    Use when the player uses or loses items.

    Args:
        item_name: Name of the item
        quantity: Number to remove

    Examples:
        - Use potion: item_name="Healing Potion"
        - Give rope: item_name="Rope (50 ft)"
        - Shoot arrows: item_name="Arrows", quantity=2
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="remove_item",
            parameters={"item_name": item_name, "quantity": quantity},
        )
    )

    # Execute the remove item command and get the result
    result = await event_bus.execute_command(
        RemoveItemCommand(game_id=game_state.game_id, item_name=item_name, quantity=quantity)
    )

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "remove_item", "item": item_name, "quantity": quantity}
