"""Inventory and currency management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.models.dependencies import AgentDependencies

logger = logging.getLogger(__name__)


async def modify_currency(
    ctx: RunContext[AgentDependencies], gold: int = 0, silver: int = 0, copper: int = 0
) -> dict[str, Any]:
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
    game_service = ctx.deps.game_service
    character = game_state.character

    old_currency = {
        "gold": character.currency.gold,
        "silver": character.currency.silver,
        "copper": character.currency.copper,
    }

    character.currency.gold = max(0, character.currency.gold + gold)
    character.currency.silver = max(0, character.currency.silver + silver)
    character.currency.copper = max(0, character.currency.copper + copper)

    new_currency = {
        "gold": character.currency.gold,
        "silver": character.currency.silver,
        "copper": character.currency.copper,
    }

    game_service.save_game(game_state)

    result = {
        "type": "currency_update",
        "old_currency": old_currency,
        "new_currency": new_currency,
        "change": {"gold": gold, "silver": silver, "copper": copper},
    }

    logger.info(
        f"Currency: {gold}gp, {silver}sp, {copper}cp - Total: {new_currency['gold']}gp, {new_currency['silver']}sp, {new_currency['copper']}cp"
    )
    return result


async def add_item(ctx: RunContext[AgentDependencies], item_name: str, quantity: int = 1) -> dict[str, Any]:
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
    game_service = ctx.deps.game_service
    character = game_state.character

    # Check if item exists
    existing = next((item for item in character.inventory if item.name == item_name), None)

    if existing:
        existing.quantity += quantity
    else:
        from app.models.character import Item

        new_item = Item(name=item_name, quantity=quantity, weight=0.0, value=0)
        character.inventory.append(new_item)

    game_service.save_game(game_state)

    result = {"type": "add_item", "item": item_name, "quantity": quantity, "success": True}

    logger.info(f"Item Added: {quantity}x {item_name} added to inventory")
    return result


async def remove_item(ctx: RunContext[AgentDependencies], item_name: str, quantity: int = 1) -> dict[str, Any]:
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
    game_service = ctx.deps.game_service
    character = game_state.character

    item = next((item for item in character.inventory if item.name == item_name), None)
    removed = False

    if item and item.quantity >= quantity:
        item.quantity -= quantity
        if item.quantity == 0:
            character.inventory.remove(item)
        removed = True

    game_service.save_game(game_state)

    result = {"type": "remove_item", "item": item_name, "quantity": quantity, "removed": removed}

    logger.info(f"Item Removed: {quantity}x {item_name} {'removed' if removed else 'not found'}")
    return result
