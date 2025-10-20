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
    entity_id: str,
    entity_type: str,
    gold: int = 0,
    silver: int = 0,
    copper: int = 0,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Modify currency for a character (player or NPC).

    Use when an entity gains or spends money. Only works with player and NPC entities.

    Args:
        entity_id: Instance ID of the entity
        entity_type: One of 'player' | 'npc' (monsters not supported)
        gold: Gold pieces to add (negative to remove)
        silver: Silver pieces to add (negative to remove)
        copper: Copper pieces to add (negative to remove)

    Examples:
        - Player finds treasure: entity_type="player", entity_id="<player-id>", gold=5, silver=10
        - NPC buys item: entity_type="npc", entity_id="<npc-id>", gold=-3
        - Player tavern tip: entity_type="player", entity_id="<player-id>", silver=-5, copper=-2
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(ModifyInventoryCommand)
async def modify_inventory(
    ctx: RunContext[AgentDependencies], entity_id: str, entity_type: str, item_index: str, quantity: int
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Add or remove items from a character's inventory (player or NPC).

    Only works with player and NPC entities. Monsters cannot carry inventory.

    Args:
        entity_id: Instance ID of the entity
        entity_type: One of 'player' | 'npc' (monsters not supported)
        item_index: The index identifier of the item to modify (e.g., "potion-of-healing", "rope-hempen-50-feet")
        quantity: The number of items to add (positive) or remove (negative)

    Examples:
        - Player finds potion: entity_type="player", entity_id="<player-id>", item_index="potion-of-healing", quantity=1
        - NPC uses potion: entity_type="npc", entity_id="<npc-id>", item_index="potion-of-healing", quantity=-1
        - Player buys rope: entity_type="player", entity_id="<player-id>", item_index="rope-hempen-50-feet", quantity=1
        - NPC gives rope away: entity_type="npc", entity_id="<npc-id>", item_index="rope-hempen-50-feet", quantity=-1
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(EquipItemCommand)
async def equip_item(
    ctx: RunContext[AgentDependencies],
    entity_id: str,
    entity_type: str,
    item_index: str,
    slot: str | None = None,
    unequip: bool = False,
) -> BaseModel:
    # Note: The return type is BaseModel as required by the pydantic-ai tool interface.
    """Equip or unequip an item for a character (player or NPC).

    Only works with player and NPC entities. Monsters use different equipment mechanics.

    Args:
        entity_id: Instance ID of the entity
        entity_type: One of 'player' | 'npc' (monsters not supported)
        item_index: Item to equip/unequip
        slot: Target slot (main_hand, off_hand, chest, etc). Auto-selects if not specified.
        unequip: True to remove from all slots

    Examples:
        - Player equips sword: entity_type="player", entity_id="<player-id>", item_index="longsword"
        - NPC dual-wields: entity_type="npc", entity_id="<npc-id>", item_index="shortsword", slot="off_hand"
        - Player unequips armor: entity_type="player", entity_id="<player-id>", item_index="leather-armor", unequip=True
        - NPC equips shield: entity_type="npc", entity_id="<npc-id>", item_index="shield", slot="off_hand"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
