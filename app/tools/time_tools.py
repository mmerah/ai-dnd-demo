"""Time management and rest tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.models.dependencies import AgentDependencies

logger = logging.getLogger(__name__)


async def short_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    """Take a short rest (1 hour).

    Allows the player to spend hit dice to recover HP.

    Examples:
        - After combat to recover
        - Before entering dangerous area
        - When wounded but time is limited
    """
    game_state = ctx.deps.game_state
    game_service = ctx.deps.game_service
    dice_service = ctx.deps.dice_service
    character = game_state.character

    # Advance time by 1 hour
    game_state.game_time.hour += 1
    if game_state.game_time.hour >= 24:
        game_state.game_time.hour -= 24
        game_state.game_time.day += 1

    old_hp = character.hit_points.current

    # Use hit dice if injured
    if character.hit_points.current < character.hit_points.maximum:
        con_mod = (character.abilities.CON - 10) // 2
        healing = dice_service.roll_dice(f"1d10+{con_mod}")
        new_hp = min(character.hit_points.maximum, character.hit_points.current + healing.total)
        character.hit_points.current = new_hp
    else:
        new_hp = old_hp

    game_service.save_game(game_state)

    result = {
        "type": "short_rest",
        "duration": "1 hour",
        "hp_restored": new_hp - old_hp,
        "old_hp": old_hp,
        "new_hp": new_hp,
        "time": f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}",
    }

    logger.info(f"Short Rest: Restored {new_hp - old_hp} HP")
    return result


async def long_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    """Take a long rest (8 hours).

    Restores all HP, spell slots, and removes most conditions.

    Examples:
        - End of adventuring day
        - After major battle
        - When severely wounded or out of resources
    """
    game_state = ctx.deps.game_state
    game_service = ctx.deps.game_service
    character = game_state.character

    # Advance time by 8 hours
    game_state.game_time.hour += 8
    if game_state.game_time.hour >= 24:
        game_state.game_time.hour -= 24
        game_state.game_time.day += 1

    # Restore all HP
    old_hp = character.hit_points.current
    character.hit_points.current = character.hit_points.maximum

    # Restore spell slots
    spell_slots_restored = False
    if character.spellcasting:
        for slot in character.spellcasting.spell_slots.values():
            slot.current = slot.total
        spell_slots_restored = True

    # Clear conditions
    conditions_removed = []
    for condition in ["exhaustion", "poisoned", "frightened", "charmed"]:
        if condition in character.conditions:
            character.conditions.remove(condition)
            conditions_removed.append(condition)

    game_service.save_game(game_state)

    result = {
        "type": "long_rest",
        "duration": "8 hours",
        "hp_restored": character.hit_points.maximum - old_hp,
        "hp_full": True,
        "spell_slots_restored": spell_slots_restored,
        "conditions_removed": conditions_removed,
        "time": f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}",
    }

    logger.info("Long Rest: Full recovery completed")
    return result


async def advance_time(ctx: RunContext[AgentDependencies], minutes: int) -> dict[str, Any]:
    """Advance game time by minutes.

    Use for travel, waiting, or other time-consuming activities.

    Args:
        minutes: Number of minutes to advance

    Examples:
        - Short travel: minutes=30
        - Searching room: minutes=10
        - Waiting for NPC: minutes=45
    """
    game_state = ctx.deps.game_state
    game_service = ctx.deps.game_service

    old_time = f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"

    total_minutes = game_state.game_time.minute + minutes
    hours_to_add = total_minutes // 60
    game_state.game_time.minute = total_minutes % 60

    total_hours = game_state.game_time.hour + hours_to_add
    days_to_add = total_hours // 24
    game_state.game_time.hour = total_hours % 24

    game_state.game_time.day += days_to_add

    new_time = f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"

    game_service.save_game(game_state)

    result = {"type": "advance_time", "minutes": minutes, "old_time": old_time, "new_time": new_time}

    logger.info(f"Time Advanced: {minutes} minutes - Now: {new_time}")
    return result
