"""Dice and combat-related tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastToolCallCommand
from app.events.commands.dice_commands import RollDiceCommand

logger = logging.getLogger(__name__)


async def roll_ability_check(
    ctx: RunContext[AgentDependencies],
    ability: str,
    skill: str | None = None,
    dc: int = 15,
    advantage: str | None = None,
    target: str = "player",
) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Calculate modifier based on character stats
    modifier = 0
    if target == "player":
        character = game_state.character
        ability_scores = {
            "STR": character.abilities.STR,
            "DEX": character.abilities.DEX,
            "CON": character.abilities.CON,
            "INT": character.abilities.INT,
            "WIS": character.abilities.WIS,
            "CHA": character.abilities.CHA,
        }
        ability_score = ability_scores.get(ability.upper(), 10)
        modifier = (ability_score - 10) // 2

        if skill and skill in character.skills:
            modifier += character.proficiency_bonus

    # Determine dice based on advantage/disadvantage
    dice = "2d20kh" if advantage == "advantage" else "2d20kl" if advantage == "disadvantage" else "1d20"

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="roll_ability_check",
            parameters={"ability": ability, "skill": skill, "dc": dc, "advantage": advantage, "target": target},
        )
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(
            game_id=game_state.game_id,
            roll_type="ability_check",
            dice=dice,
            modifier=modifier,
            target=target,
            ability=ability,
            skill=skill,
        )
    )

    # Return the actual result with DC information
    if result:
        result["dc"] = dc  # Add DC to the result
        return result
    else:
        return {
            "type": "ability_check",
            "ability": ability,
            "skill": skill,
            "target": target,
            "dc": dc,
        }


async def roll_saving_throw(
    ctx: RunContext[AgentDependencies], ability: str, dc: int = 15, advantage: str | None = None, target: str = "player"
) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Calculate modifier based on character's saving throws
    modifier = 0
    if target == "player":
        character = game_state.character
        modifier = character.saving_throws.get(ability.upper(), 0)

    # Determine dice based on advantage/disadvantage
    dice = "2d20kh" if advantage == "advantage" else "2d20kl" if advantage == "disadvantage" else "1d20"

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="roll_saving_throw",
            parameters={"ability": ability, "dc": dc, "advantage": advantage, "target": target},
        )
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(
            game_id=game_state.game_id,
            roll_type="saving_throw",
            dice=dice,
            modifier=modifier,
            target=target,
            ability=ability,
        )
    )

    # Return the actual result with DC information
    if result:
        result["dc"] = dc  # Add DC to the result
        return result
    else:
        return {"type": "saving_throw", "ability": ability, "target": target, "dc": dc}


async def roll_attack(
    ctx: RunContext[AgentDependencies],
    weapon_name: str,
    target: str,
    advantage: str | None = None,
    attacker: str = "player",
) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Calculate attack modifier
    modifier = 0
    if attacker == "player":
        character = game_state.character
        weapon = next((atk for atk in character.attacks if atk.name.lower() == weapon_name.lower()), None)

        if weapon:
            modifier = weapon.to_hit
        else:
            dex_mod = (character.abilities.DEX - 10) // 2
            str_mod = (character.abilities.STR - 10) // 2
            modifier = max(dex_mod, str_mod) + character.proficiency_bonus

    # Determine dice based on advantage/disadvantage
    dice = "2d20kh" if advantage == "advantage" else "2d20kl" if advantage == "disadvantage" else "1d20"

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="roll_attack",
            parameters={"weapon_name": weapon_name, "target": target, "advantage": advantage, "attacker": attacker},
        )
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(game_id=game_state.game_id, roll_type="attack", dice=dice, modifier=modifier, target=target)
    )

    # Return the actual result with weapon and attacker info
    if result:
        result["weapon_name"] = weapon_name
        result["attacker"] = attacker
        return result
    else:
        return {"type": "attack", "weapon_name": weapon_name, "attacker": attacker, "target": target}


async def roll_damage(
    ctx: RunContext[AgentDependencies],
    damage_dice: str,
    damage_type: str = "slashing",
    critical: bool = False,
    source: str = "weapon",
) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Roll damage for an attack or effect.

    Use after a successful attack or when damage occurs.

    Args:
        damage_dice: Dice formula (e.g., "1d8+3", "2d6")
        damage_type: Type of damage (slashing, piercing, fire, etc.)
        critical: Whether this is a critical hit (doubles dice)
        source: Source of damage (weapon, spell, environmental)

    Examples:
        - Longsword damage: damage_dice="1d8+3", damage_type="slashing"
        - Critical hit: damage_dice="1d8+3", critical=True
        - Fireball spell: damage_dice="8d6", damage_type="fire", source="spell"
        - Falling damage: damage_dice="2d6", damage_type="bludgeoning", source="environmental"
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Double dice for critical hits
    if critical:
        # Parse the damage dice to double the dice portion
        import re

        match = re.match(r"(\d+)d(\d+)([+-]\d+)?", damage_dice)
        if match:
            num_dice = int(match.group(1)) * 2
            die_size = match.group(2)
            modifier = match.group(3) or ""
            damage_dice = f"{num_dice}d{die_size}{modifier}"

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id,
            tool_name="roll_damage",
            parameters={"damage_dice": damage_dice, "damage_type": damage_type, "critical": critical, "source": source},
        )
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(
            game_id=game_state.game_id, roll_type="damage", dice=damage_dice, modifier=0, damage_type=damage_type
        )
    )

    # Return the actual result with critical and source info
    if result:
        result["critical"] = critical
        result["source"] = source
        return result
    else:
        return {
            "type": "damage",
            "damage_dice": damage_dice,
            "damage_type": damage_type,
            "critical": critical,
            "source": source,
        }


async def roll_initiative(ctx: RunContext[AgentDependencies], combatants: list[str]) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Roll initiative for combat.

    Use at the start of combat to determine turn order.

    Args:
        combatants: List of character/NPC names in combat

    Examples:
        - Start of combat: combatants=["player", "Goblin", "Wolf"]
        - Ambush scenario: combatants=["player", "Bandit1", "Bandit2", "Bandit3"]
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Player always has their dexterity modifier for initiative
    modifier = 0
    if "player" in combatants:
        character = game_state.character
        modifier = (character.abilities.DEX - 10) // 2

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(
            game_id=game_state.game_id, tool_name="roll_initiative", parameters={"combatants": combatants}
        )
    )

    # Execute the roll command and get the result
    result = await event_bus.execute_command(
        RollDiceCommand(game_id=game_state.game_id, roll_type="initiative", dice="1d20", modifier=modifier)
    )

    # Return the actual result with combatants info
    if result:
        result["combatants"] = combatants
        return result
    else:
        return {"type": "initiative", "combatants": combatants}
