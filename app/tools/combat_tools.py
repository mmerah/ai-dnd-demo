"""Combat initialization tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.combat_commands import (
    AddParticipantCommand,
    EndCombatCommand,
    NextTurnCommand,
    RemoveParticipantCommand,
    SpawnMonstersCommand,
    StartCombatCommand,
    TriggerScenarioEncounterCommand,
)
from app.models.combat import CombatParticipant, MonsterSpawnInfo
from app.models.entity import EntityType
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartCombatCommand)
async def start_combat(ctx: RunContext[AgentDependencies], npcs: list[CombatParticipant]) -> BaseModel:
    """Initialize combat with specific entities by ID.

    Use when combat begins with known enemies already present in the game state.

    Args:
        npcs: List of CombatParticipant with entity_id and entity_type set. Name is for display; initiative optional.

    Examples:
        - Ambush by goblins:
            npcs=[CombatParticipant(entity_id="<id1>", entity_type="monster", name="Goblin"),
                  CombatParticipant(entity_id="<id2>", entity_type="monster", name="Goblin")]
        - Boss fight (pre-rolled initiative):
            npcs=[CombatParticipant(entity_id="<boss-id>", entity_type="monster", name="Hobgoblin Boss", initiative=18)]
        - Mixed enemies (include NPC ally):
            npcs=[CombatParticipant(entity_id="<wolf-id>", entity_type="monster", name="Wolf"),
                  CombatParticipant(entity_id="<npc-id>", entity_type="npc", name="Guard Captain")]
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


@tool_handler(NextTurnCommand)
async def next_turn(ctx: RunContext[AgentDependencies]) -> BaseModel:
    """Advance combat to the next turn.

    Use during combat to rotate to the next participant and increment the round as needed.
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(EndCombatCommand)
async def end_combat(ctx: RunContext[AgentDependencies]) -> BaseModel:
    """End the current combat encounter and clean up defeated monsters."""
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(AddParticipantCommand)
async def add_combatant(ctx: RunContext[AgentDependencies], entity_id: str, entity_type: EntityType) -> BaseModel:
    """Add a participant to the current combat by entity id and type.

    Args:
        entity_id: Instance ID of the combatant
        entity_type: 'player' | 'npc' | 'monster'
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(RemoveParticipantCommand)
async def remove_combatant(ctx: RunContext[AgentDependencies], entity_id: str) -> BaseModel:
    """Remove a participant from combat by entity id."""
    raise NotImplementedError("This is handled by the @tool_handler decorator")
