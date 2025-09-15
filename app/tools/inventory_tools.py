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
async def modify_inventory(ctx: RunContext[AgentDependencies], item_index: str, quantity: int) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove items from the player's inventory.

    Args:
        item_index: The index identifier of the item to modify (e.g., "potion-of-healing", "rope-hempen-50-feet")
        quantity: The number of items to add (positive) or remove (negative)

    Examples:
        - Find potion: item_index="potion-of-healing", quantity=1
        - Use potion: item_index="potion-of-healing", quantity=-1
        - Buy rope: item_index="rope-hempen-50-feet", quantity=1
        - Give rope away: item_index="rope-hempen-50-feet", quantity=-1
        - Loot arrows: item_index="arrow", quantity=20
        - Shoot arrows: item_index="arrow", quantity=-2
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(EquipItemCommand)
async def equip_item(
    ctx: RunContext[AgentDependencies], item_index: str, slot: str | None = None, unequip: bool = False
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Equip or unequip an item.

    Args:
        item_index: Item to equip/unequip
        slot: Target slot (main_hand, off_hand, chest, etc). Auto-selects if not specified.
        unequip: True to remove from all slots

    Examples:
        - Equip sword: item_index="longsword"
        - Dual-wield: item_index="shortsword", slot="off_hand"
        - Unequip armor: item_index="leather-armor", unequip=True
        - Equip shield in off-hand: item_index="shield", slot="off_hand"
        - Wear amulet: item_index="amulet-of-health", slot="neck"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
