"""Inventory management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.inventory_commands import (
    AddItemCommand,
    ModifyCurrencyCommand,
    RemoveItemCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(ModifyCurrencyCommand)
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
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(AddItemCommand)
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
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(RemoveItemCommand)
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
    raise NotImplementedError("This is handled by the @tool_handler decorator")
