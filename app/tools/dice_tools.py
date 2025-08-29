"""Dice and combat-related tools for D&D 5e AI Dungeon Master."""

from typing import Dict, Any, Optional
import re
from pydantic_ai import RunContext
from app.models.dependencies import AgentDependencies
from app.services.dice_service import DiceService, RollType
import logging

logger = logging.getLogger(__name__)


async def roll_ability_check(
    ctx: RunContext[AgentDependencies],
    ability: str,
    skill: Optional[str] = None,
    dc: int = 15,
    advantage: Optional[str] = None,
    target: str = "player"
) -> Dict[str, Any]:
    """Roll an ability check for D&D 5e.
    
    Use this when a character attempts an action requiring an ability check.
    
    Args:
        ability: Ability score (STR, DEX, CON, INT, WIS, CHA)
        skill: Optional skill name (e.g., Athletics, Stealth, Perception)
        dc: Difficulty Class - 10 (Easy), 15 (Medium), 20 (Hard), 25 (Very Hard)
        advantage: 'advantage', 'disadvantage', or None for normal
        target: 'player' or NPC name making the check
    
    Examples:
        - Climbing a cliff: ability="STR", skill="Athletics", dc=15
        - Sneaking past guards: ability="DEX", skill="Stealth", dc=12
        - Searching for traps: ability="WIS", skill="Perception", dc=15
        - Recalling lore: ability="INT", skill="History", dc=10
    """
    dice_service = ctx.deps.dice_service
    game_state = ctx.deps.game_state
    
    roll_type = RollType.NORMAL
    if advantage == "advantage":
        roll_type = RollType.ADVANTAGE
    elif advantage == "disadvantage":
        roll_type = RollType.DISADVANTAGE
    
    modifier = 0
    proficiency_bonus = 0
    
    if target == "player":
        character = game_state.character
        ability_scores = {
            "STR": character.abilities.STR,
            "DEX": character.abilities.DEX,
            "CON": character.abilities.CON,
            "INT": character.abilities.INT,
            "WIS": character.abilities.WIS,
            "CHA": character.abilities.CHA
        }
        
        ability_score = ability_scores.get(ability.upper(), 10)
        modifier = (ability_score - 10) // 2
        
        if skill and skill in character.skills:
            proficiency_bonus = character.proficiency_bonus
    
    total_modifier = modifier + proficiency_bonus
    formula = f"1d20{'+' if total_modifier >= 0 else ''}{total_modifier}"
    roll_result = dice_service.roll_dice(formula, roll_type)
    
    success = roll_result.total >= dc
    
    result = {
        "type": "ability_check",
        "ability": ability,
        "skill": skill,
        "target": target,
        "dc": dc,
        "roll": roll_result.total,
        "natural_roll": roll_result.rolls[0] if roll_result.rolls else 0,
        "modifier": total_modifier,
        "proficiency_bonus": proficiency_bonus,
        "success": success,
        "critical_success": roll_result.is_critical_success,
        "critical_failure": roll_result.is_critical_failure,
        "formula": formula
    }
    
    logger.info(f"Ability check: {target} rolled {ability} {'(' + skill + ')' if skill else ''} - {roll_result.total} vs DC {dc} - {'Success' if success else 'Failure'}")
    return result


async def roll_saving_throw(
    ctx: RunContext[AgentDependencies],
    ability: str,
    dc: int = 15,
    advantage: Optional[str] = None,
    target: str = "player"
) -> Dict[str, Any]:
    """Roll a saving throw for D&D 5e.
    
    Use when a character must resist an effect or avoid danger.
    
    Args:
        ability: Ability for the save (STR, DEX, CON, INT, WIS, CHA)
        dc: Difficulty Class to meet or beat
        advantage: 'advantage', 'disadvantage', or None
        target: 'player' or NPC name making the save
    
    Examples:
        - Dodging a trap: ability="DEX", dc=14
        - Resisting poison: ability="CON", dc=12
        - Fighting off charm: ability="WIS", dc=13
        - Withstanding fear: ability="WIS", dc=10
    """
    dice_service = ctx.deps.dice_service
    game_state = ctx.deps.game_state
    
    roll_type = RollType.NORMAL
    if advantage == "advantage":
        roll_type = RollType.ADVANTAGE
    elif advantage == "disadvantage":
        roll_type = RollType.DISADVANTAGE
    
    modifier = 0
    
    if target == "player":
        character = game_state.character
        modifier = character.saving_throws.get(ability.upper(), 0)
    
    formula = f"1d20{'+' if modifier >= 0 else ''}{modifier}"
    roll_result = dice_service.roll_dice(formula, roll_type)
    success = roll_result.total >= dc
    
    result = {
        "type": "saving_throw",
        "ability": ability,
        "target": target,
        "dc": dc,
        "roll": roll_result.total,
        "natural_roll": roll_result.rolls[0] if roll_result.rolls else 0,
        "modifier": modifier,
        "success": success,
        "critical_success": roll_result.is_critical_success,
        "critical_failure": roll_result.is_critical_failure,
        "formula": formula
    }
    
    logger.info(f"Saving throw: {target} rolled {ability} save - {roll_result.total} vs DC {dc} - {'Success' if success else 'Failure'}")
    return result


async def roll_attack(
    ctx: RunContext[AgentDependencies],
    weapon_name: str,
    target: str,
    advantage: Optional[str] = None,
    attacker: str = "player"
) -> Dict[str, Any]:
    """Roll an attack in combat.
    
    Use when a character or NPC makes an attack.
    
    Args:
        weapon_name: Name of the weapon being used
        target: Name of the target being attacked
        advantage: 'advantage', 'disadvantage', or None
        attacker: 'player' or NPC name making the attack
    
    Examples:
        - Player attacks goblin: weapon_name="Longsword", target="Goblin"
        - Goblin attacks player: weapon_name="Scimitar", target="player", attacker="Goblin"
        - Ranged attack: weapon_name="Longbow", target="Orc"
    """
    dice_service = ctx.deps.dice_service
    game_state = ctx.deps.game_state
    
    roll_type = RollType.NORMAL
    if advantage == "advantage":
        roll_type = RollType.ADVANTAGE
    elif advantage == "disadvantage":
        roll_type = RollType.DISADVANTAGE
    
    modifier = 0
    target_ac = 10
    
    if attacker == "player":
        character = game_state.character
        weapon = next((atk for atk in character.attacks if atk.name.lower() == weapon_name.lower()), None)
        
        if weapon:
            modifier = weapon.to_hit
        else:
            dex_mod = (character.abilities.DEX - 10) // 2
            str_mod = (character.abilities.STR - 10) // 2
            modifier = max(dex_mod, str_mod) + character.proficiency_bonus
    
    if target != "player":
        npc = next((n for n in game_state.npcs if n.name.lower() == target.lower()), None)
        if npc:
            target_ac = npc.armor_class
    else:
        target_ac = game_state.character.armor_class
    
    formula = f"1d20{'+' if modifier >= 0 else ''}{modifier}"
    roll_result = dice_service.roll_dice(formula, roll_type)
    hit = roll_result.is_critical_success or (not roll_result.is_critical_failure and roll_result.total >= target_ac)
    
    result = {
        "type": "attack_roll",
        "attacker": attacker,
        "weapon": weapon_name,
        "target": target,
        "target_ac": target_ac,
        "roll": roll_result.total,
        "natural_roll": roll_result.rolls[0] if roll_result.rolls else 0,
        "modifier": modifier,
        "hit": hit,
        "critical_hit": roll_result.is_critical_success,
        "critical_miss": roll_result.is_critical_failure,
        "formula": formula
    }
    
    logger.info(f"Attack: {attacker} attacks {target} with {weapon_name} - {roll_result.total} vs AC {target_ac} - {'HIT' if hit else 'MISS'}")
    return result


async def roll_damage(
    ctx: RunContext[AgentDependencies],
    damage_dice: str,
    damage_type: str,
    is_critical: bool = False
) -> Dict[str, Any]:
    """Roll damage for an attack or effect.
    
    Use after a successful attack or for spell/environmental damage.
    
    Args:
        damage_dice: Dice formula (e.g., "1d8+3", "2d6", "1d4+1")
        damage_type: Type of damage (slashing, piercing, fire, etc.)
        is_critical: Whether this is a critical hit (doubles dice)
    
    Examples:
        - Longsword hit: damage_dice="1d8+3", damage_type="slashing"
        - Critical hit: damage_dice="1d8+3", damage_type="slashing", is_critical=True
        - Fire spell: damage_dice="3d6", damage_type="fire"
        - Fall damage: damage_dice="2d6", damage_type="bludgeoning"
    """
    dice_service = ctx.deps.dice_service
    
    if is_critical:
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', damage_dice)
        if match:
            dice_count = int(match.group(1)) * 2
            dice_sides = match.group(2)
            modifier = match.group(3) or ''
            damage_dice = f"{dice_count}d{dice_sides}{modifier}"
    
    roll_result = dice_service.roll_dice(damage_dice)
    
    result = {
        "type": "damage_roll",
        "damage_type": damage_type,
        "roll": roll_result.total,
        "dice_rolls": roll_result.rolls,
        "is_critical": is_critical,
        "formula": damage_dice
    }
    
    logger.info(f"Damage roll: {damage_dice} = {roll_result.total} {damage_type} damage {'(CRITICAL!)' if is_critical else ''}")
    return result


async def roll_initiative(
    ctx: RunContext[AgentDependencies],
    target: str = "player"
) -> Dict[str, Any]:
    """Roll initiative for combat.
    
    Use at the start of combat to determine turn order.
    
    Args:
        target: 'player' or NPC name rolling initiative
    
    Examples:
        - Player rolls: target="player"
        - Goblin rolls: target="Goblin"
        - Multiple NPCs: call once for each NPC
    """
    dice_service = ctx.deps.dice_service
    game_state = ctx.deps.game_state
    
    modifier = 0
    
    if target == "player":
        character = game_state.character
        modifier = character.initiative
    else:
        npc = next((n for n in game_state.npcs if n.name.lower() == target.lower()), None)
        if npc:
            modifier = 2  # Default NPC initiative modifier
    
    formula = f"1d20{'+' if modifier >= 0 else ''}{modifier}"
    roll_result = dice_service.roll_dice(formula)
    
    result = {
        "type": "initiative_roll",
        "target": target,
        "roll": roll_result.total,
        "natural_roll": roll_result.rolls[0] if roll_result.rolls else 0,
        "modifier": modifier,
        "formula": formula
    }
    
    logger.info(f"Initiative: {target} rolled {roll_result.total}")
    return result