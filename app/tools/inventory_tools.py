"""Inventory management tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.inventory_commands import (
    EquipItemCommand,
    ModifyCurrencyCommand,
    ModifyInventoryCommand,
)
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


@tool_handler(ModifyInventoryCommand)
async def modify_inventory(ctx: RunContext[AgentDependencies], item_name: str, quantity: int) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove items from the player's inventory.

    Args:
        item_name: The name of the item to modify
        quantity: The number of items to add (positive) or remove (negative)

    Examples:
        - Find potion: item_name="Potion of Healing", quantity=1
        - Use potion: item_name="Potion of Healing", quantity=-1
        - Buy rope: item_name="Rope, hempen (50 feet)", quantity=1
        - Give rope away: item_name="Rope, hempen (50 feet)", quantity=-1
        - Loot arrows: item_name="Arrows", quantity=20
        - Shoot arrows: item_name="Arrows", quantity=-2
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(EquipItemCommand)
async def equip_item(ctx: RunContext[AgentDependencies], item_name: str, equipped: bool = True) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Equip or unequip an item in the player's inventory.

    Args:
        item_name: The name of the item to equip/unequip
        equipped: True to equip, False to unequip

    Examples:
        - Equip a sword: item_name="Longsword", equipped=True
        - Unequip armor: item_name="Leather Armor", equipped=False
        - Put on a shield: item_name="Shield", equipped=True
        - Take off a helmet: item_name="Helmet", equipped=False
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
