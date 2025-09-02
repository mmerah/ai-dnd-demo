"""Combat initialization tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.combat_commands import (
    SpawnMonstersCommand,
    StartCombatCommand,
    TriggerScenarioEncounterCommand,
)
from app.models.combat import CombatParticipant, MonsterSpawnInfo
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartCombatCommand)
async def start_combat(ctx: RunContext[AgentDependencies], npcs: list[CombatParticipant]) -> BaseModel:
    """Initialize combat with specific NPCs or monsters.

    Use when combat begins with known enemies.

    Args:
        npcs: List of CombatParticipant objects with name and optional initiative

    Examples:
        - Ambush by goblins: npcs=[CombatParticipant(name="Goblin 1"), CombatParticipant(name="Goblin 2")]
        - Boss fight: npcs=[CombatParticipant(name="Hobgoblin Boss", initiative=18)]
        - Mixed enemies: npcs=[CombatParticipant(name="Wolf"), CombatParticipant(name="Goblin Scout")]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(TriggerScenarioEncounterCommand)
async def trigger_scenario_encounter(ctx: RunContext[AgentDependencies], encounter_id: str) -> BaseModel:
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
async def spawn_monsters(ctx: RunContext[AgentDependencies], monsters: list[MonsterSpawnInfo]) -> BaseModel:
    """Spawn monsters from the database.

    Use when adding monsters to the game from the monster database.

    Args:
        monsters: List of MonsterSpawnInfo objects with monster_name and quantity

    Examples:
        - Goblin patrol: monsters=[MonsterSpawnInfo(monster_name="Goblin", quantity=3)]
        - Wolf pack: monsters=[MonsterSpawnInfo(monster_name="Wolf", quantity=2)]
        - Mixed group: monsters=[MonsterSpawnInfo(monster_name="Hobgoblin", quantity=1), MonsterSpawnInfo(monster_name="Goblin", quantity=2)]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
