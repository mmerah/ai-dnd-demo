"""Decorators for tool functions to reduce boilerplate."""

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, cast

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.base import BaseCommand
from app.events.commands.broadcast_commands import BroadcastToolCallCommand, BroadcastToolResultCommand
from app.models.tool_results import ToolResult


def tool_handler(command_class: type[BaseCommand]) -> Callable[..., Callable[..., Coroutine[Any, Any, BaseModel]]]:
    """
    Decorator to handle common tool boilerplate.

    Automatically:
    1. Broadcasts the tool call
    2. Executes the domain command
    3. Returns the result or fallback

    Args:
        command_class: The command class to execute for this tool
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, BaseModel]],
    ) -> Callable[..., Coroutine[Any, Any, BaseModel]]:
        @wraps(func)
        async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
            game_state = ctx.deps.game_state
            event_bus = ctx.deps.event_bus
            tool_name = func.__name__

            # 1. Broadcast tool call
            await event_bus.submit_command(
                BroadcastToolCallCommand(game_id=game_state.game_id, tool_name=tool_name, parameters=kwargs),
            )

            # 2. Execute domain command
            command = command_class(game_id=game_state.game_id, **kwargs)
            result = await event_bus.execute_command(command)

            # 3. Broadcast tool result
            if result:
                # Cast to ToolResult since we know all tool handlers return ToolResult subtypes
                tool_result = cast(ToolResult, result)
                await event_bus.submit_command(
                    BroadcastToolResultCommand(game_id=game_state.game_id, tool_name=tool_name, result=tool_result),
                )
                return result
            # No result is a serious error - commands should always return something
            raise RuntimeError(f"Command {command_class.__name__} returned None for tool {tool_name}")

        # Preserve the original function's metadata
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__

        return wrapper

    return decorator
