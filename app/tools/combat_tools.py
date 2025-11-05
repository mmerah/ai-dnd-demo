"""Combat management tools for D&D 5e AI Dungeon Master.

IMPORTANT: Tools are agent-specific:
- NARRATIVE AGENT: start_combat, start_encounter_combat, spawn_monsters
- COMBAT AGENT: next_turn, end_combat, add_combatant, remove_combatant

The narrative agent MUST STOP after calling start_combat/start_encounter_combat.
"""

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
    StartEncounterCombatCommand,
)
from app.models.attributes import EntityType
from app.models.combat import MonsterSpawnInfo
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartCombatCommand)
async def start_combat(ctx: RunContext[AgentDependencies], entity_ids: list[str]) -> BaseModel:
    """Start combat with existing entities by their instance IDs.

    **NARRATIVE AGENT ONLY**: This tool starts combat and hands control to the combat agent.
    After calling this tool, the narrative agent MUST STOP IMMEDIATELY.

    Use for unscripted fights with entities already present at the player's current location
    (e.g., spawned earlier, notable monsters, or nearby NPCs).

    Args:
        entity_ids: List of instance IDs to include in combat (monsters and/or NPCs).

    Examples:
        - Goblin skirmish: entity_ids=["goblin-1234", "goblin-5678"]
        - Boss fight: entity_ids=["goblin-boss-9012"]
        - Mixed: entity_ids=["wolf-7777", "guard-captain-8888"]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(StartEncounterCombatCommand)
async def start_encounter_combat(ctx: RunContext[AgentDependencies], encounter_id: str) -> BaseModel:
    """Start a predefined encounter from the scenario.

    **NARRATIVE AGENT ONLY**: This tool starts combat and hands control to the combat agent.
    After calling this tool, the narrative agent MUST STOP IMMEDIATELY.

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

    **NARRATIVE AGENT ONLY**: Use this to add monsters before combat starts.
    Do NOT use during active combat.

    Use when adding monsters to the current location from the monster database.

    Args:
        monsters: List of MonsterSpawnInfo objects with monster_name and quantity

    Examples:
        - Goblin patrol: monsters=[MonsterSpawnInfo(monster_name="Goblin", quantity=3)]
        - Wolf pack: monsters=[MonsterSpawnInfo(monster_name="Wolf", quantity=2)]
        - Mixed group: monsters=[MonsterSpawnInfo(monster_name="Hobgoblin", quantity=1), MonsterSpawnInfo(monster_name="Goblin", quantity=2)]
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(NextTurnCommand)
async def next_turn(ctx: RunContext[AgentDependencies], **_ignored: object) -> BaseModel:
    """Advance combat to the next turn.

    **COMBAT AGENT ONLY**: This tool is exclusively for the combat agent.
    MANDATORY: Must be called after EVERY combat turn completes.

    Use during combat to rotate to the next participant and increment the round as needed.

    Note: This tool accepts no parameters. Any provided parameters are ignored.
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(EndCombatCommand)
async def end_combat(ctx: RunContext[AgentDependencies], **_ignored: object) -> BaseModel:
    """End the current combat encounter and clean up defeated monsters.

    **COMBAT AGENT ONLY**: This tool is exclusively for the combat agent.
    Call when all enemies are defeated or combat otherwise concludes.

    Note: This tool accepts no parameters. Any provided parameters are ignored.
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(AddParticipantCommand)
async def add_combatant(ctx: RunContext[AgentDependencies], entity_id: str, entity_type: EntityType) -> BaseModel:
    """Add a participant to the current combat by entity id and type.

    **COMBAT AGENT ONLY**: This tool is exclusively for the combat agent.

    Args:
        entity_id: Instance ID of the combatant
        entity_type: 'player' | 'npc' | 'monster'
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(RemoveParticipantCommand)
async def remove_combatant(ctx: RunContext[AgentDependencies], entity_id: str) -> BaseModel:
    """Remove a participant from combat by entity id.

    **COMBAT AGENT ONLY**: This tool is exclusively for the combat agent."""
    raise NotImplementedError("This is handled by the @tool_handler decorator")
