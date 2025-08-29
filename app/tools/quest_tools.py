"""Quest management tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    ProgressActCommand,
    StartQuestCommand,
)
from app.models.quest import ObjectiveStatus
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartQuestCommand)
async def start_quest(ctx: RunContext[AgentDependencies], quest_id: str) -> dict[str, Any]:
    """Activate a new quest.

    Use when the player accepts or begins a quest.

    Args:
        quest_id: ID of the quest to start

    Examples:
        - Accept main quest: quest_id="defeat_goblin_boss"
        - Start side quest: quest_id="find_missing_merchant"
        - Begin act quest: quest_id="investigate_cave"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(CompleteObjectiveCommand)
async def complete_objective(ctx: RunContext[AgentDependencies], quest_id: str, objective_id: str) -> dict[str, Any]:
    """Mark a quest objective as completed.

    Use when the player achieves a quest objective.

    Args:
        quest_id: ID of the quest
        objective_id: ID of the objective to complete

    Examples:
        - Found clue: quest_id="investigate_cave", objective_id="find_goblin_tracks"
        - Defeated enemy: quest_id="defeat_goblin_boss", objective_id="clear_entrance"
        - Rescued NPC: quest_id="rescue_mission", objective_id="find_prisoner"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(CompleteQuestCommand)
async def complete_quest(ctx: RunContext[AgentDependencies], quest_id: str) -> dict[str, Any]:
    """Complete an entire quest.

    Use when all quest objectives are done.

    Args:
        quest_id: ID of the quest to complete

    Examples:
        - Main quest done: quest_id="defeat_goblin_boss"
        - Side quest finished: quest_id="deliver_package"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(ProgressActCommand)
async def progress_act(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    """Progress to the next act of the scenario.

    Use when moving to the next chapter of the story.

    Examples:
        - After completing all act 1 quests
        - When major story milestone is reached
        - Upon defeating act boss
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


async def check_quest_prerequisites(ctx: RunContext[AgentDependencies], quest_id: str) -> dict[str, Any]:
    """Check if a quest's prerequisites are met.

    Use to verify if a quest can be started.

    Args:
        quest_id: ID of the quest to check

    Examples:
        - Check if ready for boss: quest_id="defeat_goblin_boss"
        - Verify quest availability: quest_id="advanced_quest"
    """
    deps = ctx.deps
    game_state = deps.game_state

    # Get scenario
    scenario = deps.scenario_service.get_scenario(game_state.scenario_id) if game_state.scenario_id else None
    if not scenario:
        return {"available": False, "message": "No scenario loaded"}

    # Get quest
    quest = scenario.get_quest(quest_id)
    if not quest:
        return {"available": False, "message": f"Quest '{quest_id}' not found"}

    # Check prerequisites
    is_available = quest.is_available(game_state.completed_quest_ids)

    if is_available:
        return {"available": True, "message": f"Quest '{quest.name}' is available"}
    else:
        missing = [prereq for prereq in quest.prerequisites if prereq not in game_state.completed_quest_ids]
        return {
            "available": False,
            "message": f"Quest '{quest.name}' requires completing: {', '.join(missing)}",
            "missing_prerequisites": missing,
        }


async def update_objective_status(
    ctx: RunContext[AgentDependencies], quest_id: str, objective_id: str, status: str
) -> dict[str, Any]:
    """Update the status of a quest objective.

    Use to change objective status (pending/active/completed/failed).

    Args:
        quest_id: ID of the quest
        objective_id: ID of the objective
        status: New status (pending/active/completed/failed)

    Examples:
        - Mark as active: status="active"
        - Mark as failed: status="failed"
    """
    deps = ctx.deps
    game_state = deps.game_state
    game_service = deps.game_service

    # Get the active quest
    quest = game_state.get_active_quest(quest_id)
    if not quest:
        return {"success": False, "message": f"Quest '{quest_id}' not found in active quests"}

    # Update objective status
    try:
        objective_status = ObjectiveStatus(status)
    except ValueError:
        return {"success": False, "message": f"Invalid status '{status}'"}

    if quest.update_objective(objective_id, objective_status):
        game_service.save_game(game_state)
        return {
            "success": True,
            "message": f"Objective '{objective_id}' status updated to {status}",
            "quest_status": quest.status.value,
            "progress": quest.get_progress_percentage(),
        }

    return {"success": False, "message": f"Objective '{objective_id}' not found in quest"}
