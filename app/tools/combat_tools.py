"""Combat initialization tools for D&D 5e AI Dungeon Master."""

import logging
import random
from typing import Any

from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.combat_commands import (
    SpawnMonstersCommand,
    StartCombatCommand,
    TriggerScenarioEncounterCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartCombatCommand)
async def start_combat(ctx: RunContext[AgentDependencies], npcs: list[dict[str, Any]]) -> dict[str, Any]:
    """Initialize combat with specific NPCs or monsters.

    Use when combat begins with known enemies.

    Args:
        npcs: List of NPCs with name and optional initiative
              Format: [{"name": "Goblin", "initiative": 15}, ...]

    Examples:
        - Ambush by goblins: npcs=[{"name": "Goblin 1"}, {"name": "Goblin 2"}]
        - Boss fight: npcs=[{"name": "Hobgoblin Boss", "initiative": 18}]
        - Mixed enemies: npcs=[{"name": "Wolf"}, {"name": "Goblin Scout"}]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(TriggerScenarioEncounterCommand)
async def trigger_scenario_encounter(ctx: RunContext[AgentDependencies], encounter_id: str) -> dict[str, Any]:
    """Start a predefined encounter from the scenario.

    Use when triggering specific scenario encounters.

    Args:
        encounter_id: ID of the encounter to trigger

    Examples:
        - Goblin ambush: encounter_id="forest_ambush_1"
        - Boss battle: encounter_id="boss_fight"
        - Trap triggered: encounter_id="pit_trap_1"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(SpawnMonstersCommand)
async def spawn_monsters(ctx: RunContext[AgentDependencies], monsters: list[dict[str, int]]) -> dict[str, Any]:
    """Spawn monsters from the database.

    Use when adding monsters to the game from the monster database.

    Args:
        monsters: List of monster types and quantities
                 Format: [{"monster_name": "Goblin", "quantity": 2}, ...]

    Examples:
        - Goblin patrol: monsters=[{"monster_name": "Goblin", "quantity": 3}]
        - Wolf pack: monsters=[{"monster_name": "Wolf", "quantity": 2}]
        - Mixed group: monsters=[{"monster_name": "Hobgoblin", "quantity": 1}, {"monster_name": "Goblin", "quantity": 2}]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


async def roll_group_initiative(
    ctx: RunContext[AgentDependencies], group_name: str, modifier: int = 0
) -> dict[str, Any]:
    """Roll initiative for a group of similar enemies.

    Use for groups that act together in combat.

    Args:
        group_name: Name of the group (e.g., "Goblins")
        modifier: Initiative modifier for the group

    Examples:
        - Goblin group: group_name="Goblins", modifier=2
        - Wolf pack: group_name="Wolves", modifier=2
    """
    # Roll d20 + modifier
    roll = random.randint(1, 20)
    total = roll + modifier

    result = {
        "group": group_name,
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "message": f"{group_name} initiative: {roll} + {modifier} = {total}",
    }

    # Would normally update combat state here
    return result
