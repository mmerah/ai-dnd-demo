"""Time management and rest tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

from pydantic_ai import RunContext

from app.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastToolCallCommand
from app.events.commands.time_commands import (
    AdvanceTimeCommand,
    LongRestCommand,
    ShortRestCommand,
)

logger = logging.getLogger(__name__)


async def short_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Take a short rest (1 hour).

    Allows the player to spend hit dice to recover HP.

    Examples:
        - After combat to recover
        - Before entering dangerous area
        - When wounded but time is limited
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(game_id=game_state.game_id, tool_name="short_rest", parameters={})
    )

    # Execute the short rest command and get the result
    result = await event_bus.execute_command(ShortRestCommand(game_id=game_state.game_id))

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "short_rest", "duration": "1 hour"}


async def long_rest(ctx: RunContext[AgentDependencies]) -> dict[str, Any]:
    # Note: The return type is dict[str, Any] as required by the pydantic-ai tool interface.
    """Take a long rest (8 hours).

    Restores all HP, spell slots, and removes most conditions.

    Examples:
        - End of adventuring day
        - After major battle
        - When severely wounded or out of resources
    """
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(game_id=game_state.game_id, tool_name="long_rest", parameters={})
    )

    # Execute the long rest command and get the result
    result = await event_bus.execute_command(LongRestCommand(game_id=game_state.game_id))

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "long_rest", "duration": "8 hours"}


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
    game_state = ctx.deps.game_state
    event_bus = ctx.deps.event_bus

    # Broadcast the tool call
    await event_bus.submit_command(
        BroadcastToolCallCommand(game_id=game_state.game_id, tool_name="advance_time", parameters={"minutes": minutes})
    )

    # Execute the advance time command and get the result
    result = await event_bus.execute_command(AdvanceTimeCommand(game_id=game_state.game_id, minutes=minutes))

    # Return the actual result
    if result:
        return result
    else:
        return {"type": "advance_time", "minutes": minutes}
