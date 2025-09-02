"""Quest management tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    ProgressActCommand,
    StartQuestCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(StartQuestCommand)
async def start_quest(ctx: RunContext[AgentDependencies], quest_id: str) -> BaseModel:
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
async def complete_objective(ctx: RunContext[AgentDependencies], quest_id: str, objective_id: str) -> BaseModel:
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
async def complete_quest(ctx: RunContext[AgentDependencies], quest_id: str) -> BaseModel:
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
async def progress_act(ctx: RunContext[AgentDependencies]) -> BaseModel:
    """Progress to the next act of the scenario.

    Use when moving to the next chapter of the story.

    Examples:
        - After completing all act 1 quests
        - When major story milestone is reached
        - Upon defeating act boss
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
