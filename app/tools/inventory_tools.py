"""Inventory management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import cast

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.events.base import BaseCommand
from app.agents.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastToolCallCommand, BroadcastToolResultCommand
from app.events.commands.inventory_commands import (
    AddItemCommand,
    ModifyCurrencyCommand,
    RemoveItemCommand,
)
from app.models.tool_results import ToolResult
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(ModifyCurrencyCommand)
async def modify_currency(
    ctx: RunContext[AgentDependencies],
    gold: int = 0,
    silver: int = 0,
    copper: int = 0,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
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
    raise NotImplementedError("This is handled by the @tool_handler decorator")


async def modify_inventory(ctx: RunContext[AgentDependencies], item_name: str, quantity: int) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove items from the player's inventory.

    Args:
        item_name: The name of the item to modify
        quantity: The number of items to add (positive) or remove (negative)

    Examples:
        - Find potion: item_name="Healing Potion", quantity=1
        - Use potion: item_name="Healing Potion", quantity=-1
        - Buy rope: item_name="Rope (50 ft)", quantity=1
        - Give rope away: item_name="Rope (50 ft)", quantity=-1
        - Loot arrows: item_name="Arrows", quantity=20
        - Shoot arrows: item_name="Arrows", quantity=-2
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="modify_inventory",
            parameters={"item_name": item_name, "quantity": quantity},
        ),
    )

    # Determine which command to use based on quantity
    command: BaseCommand
    if quantity > 0:
        command = AddItemCommand(game_id=game_state.game_id, item_name=item_name, quantity=quantity)
    else:
        command = RemoveItemCommand(game_id=game_state.game_id, item_name=item_name, quantity=abs(quantity))

    # Execute the command
    result = await event_bus.execute_command(command)

    if not result:
        raise RuntimeError(f"Failed to modify inventory for {item_name}")

    if not isinstance(result, BaseModel):
        raise TypeError(f"Expected BaseModel from command, got {type(result)}")

    tool_result = cast(ToolResult, result)
    await event_bus.submit_command(
        BroadcastToolResultCommand(game_id=game_state.game_id, tool_name="modify_inventory", result=tool_result),
    )

    return result
