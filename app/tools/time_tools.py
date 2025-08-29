"""Time management and rest tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.time_commands import (
    AdvanceTimeCommand,
    LongRestCommand,
    ShortRestCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(ShortRestCommand)
async def short_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Take a short rest (1 hour).

    Allows the player to spend hit dice to recover HP.

    Examples:
        - After combat to recover
        - Before entering dangerous area
        - When wounded but time is limited
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(LongRestCommand)
async def long_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Take a long rest (8 hours).

    Restores all HP, spell slots, and removes most conditions.

    Examples:
        - End of adventuring day
        - After major battle
        - When severely wounded or out of resources
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(AdvanceTimeCommand)
async def advance_time(ctx: RunContext[AgentDependencies], minutes: int) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Advance game time by minutes.

    Use for travel, waiting, or other time-consuming activities.

    Args:
        minutes: Number of minutes to advance

    Examples:
        - Short travel: minutes=30
        - Searching room: minutes=10
        - Waiting for NPC: minutes=45
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
