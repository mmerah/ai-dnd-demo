"""Character management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

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
    game_service = ctx.deps.game_service

    old_hp = 0
    new_hp = 0
    max_hp = 0

    if target == "player":
        character = game_state.character
        old_hp = character.hit_points.current
        max_hp = character.hit_points.maximum

        if amount > 0:
            new_hp = min(old_hp + amount, max_hp)
        else:
            new_hp = max(0, old_hp + amount)

        character.hit_points.current = new_hp
    else:
        npc = next((n for n in game_state.npcs if n.name.lower() == target.lower()), None)
        if npc:
            old_hp = npc.hit_points.current
            max_hp = npc.hit_points.maximum

            if amount > 0:
                new_hp = min(old_hp + amount, max_hp)
            else:
                new_hp = max(0, old_hp + amount)

            npc.hit_points.current = new_hp

    # Save game state
    game_service.save_game(game_state)

    result = {
        "type": "hp_update",
        "target": target,
        "old_hp": old_hp,
        "new_hp": new_hp,
        "max_hp": max_hp,
        "amount": amount,
        "damage_type": damage_type,
        "is_healing": amount > 0,
        "is_unconscious": new_hp == 0,
    }

    logger.info(
        f"HP Update: {target} {'healed' if amount > 0 else 'took'} {abs(amount)} {damage_type} - HP: {old_hp} → {new_hp}/{max_hp}"
    )
    return result


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
    game_service = ctx.deps.game_service

    if target == "player":
        character = game_state.character
        if condition not in character.conditions:
            character.conditions.append(condition)
    else:
        # For NPCs in combat
        if game_state.combat:
            for participant in game_state.combat.participants:
                if participant.name.lower() == target.lower():
                    if condition not in participant.conditions:
                        participant.conditions.append(condition)
                    break

    game_service.save_game(game_state)

    result = {"type": "add_condition", "target": target, "condition": condition, "duration": duration, "success": True}

    logger.info(
        f"Condition Added: {target} is now {condition} {'for ' + str(duration) + ' rounds' if duration > 0 else 'until removed'}"
    )
    return result


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
    game_service = ctx.deps.game_service
    removed = False

    if target == "player":
        character = game_state.character
        if condition in character.conditions:
            character.conditions.remove(condition)
            removed = True
    else:
        if game_state.combat:
            for participant in game_state.combat.participants:
                if participant.name.lower() == target.lower():
                    if condition in participant.conditions:
                        participant.conditions.remove(condition)
                        removed = True
                    break

    game_service.save_game(game_state)

    result = {"type": "remove_condition", "target": target, "condition": condition, "removed": removed}

    logger.info(f"Condition Removed: {target} is no longer {condition}")
    return result


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
    game_service = ctx.deps.game_service
    character = game_state.character

    if not character.spellcasting:
        return {"type": "spell_slots_update", "level": level, "error": "Character has no spellcasting ability"}

    spell_slots = character.spellcasting.spell_slots
    level_key = f"level_{level}"

    if level_key not in spell_slots:
        return {"type": "spell_slots_update", "level": level, "error": f"No spell slots for level {level}"}

    slot = spell_slots[level_key]
    old_slots = slot.current
    slot.current = max(0, min(slot.total, old_slots + amount))
    new_slots = slot.current
    max_slots = slot.total

    game_service.save_game(game_state)

    result = {
        "type": "spell_slots_update",
        "level": level,
        "old_slots": old_slots,
        "new_slots": new_slots,
        "max_slots": max_slots,
        "change": amount,
    }

    logger.info(f"Spell Slots: Level {level} - {old_slots} → {new_slots}/{max_slots}")
    return result
