"""Decorators for tool functions to reduce boilerplate."""

import logging
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, cast

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.events.commands.broadcast_commands import (
    BroadcastPolicyWarningCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.models.game_state import GameEventType

logger = logging.getLogger(__name__)


def tool_handler(
    command_class: type[BaseCommand] | None = None,
    prepare: (
        Callable[[dict[str, Any]], dict[str, Any]]
        | Callable[[dict[str, Any]], tuple[dict[str, Any], dict[str, JSONSerializable]]]
    )
    | None = None,
    command_factory: Callable[[RunContext[AgentDependencies], dict[str, Any]], BaseCommand] | None = None,
) -> Callable[..., Callable[..., Coroutine[Any, Any, BaseModel]]]:
    """
    Decorator to handle common tool boilerplate.

    Automatically:
    1. Broadcasts the tool call
    2. Persists a TOOL_CALL GameEvent
    3. Executes the domain command
    4. Broadcasts the tool result
    5. Persists a TOOL_RESULT GameEvent

    Args:
        command_class: The command class to execute for this tool
        prepare: Optional transformer for kwargs. If provided, it can:
            - return a dict of kwargs to use for command construction (broadcast uses original kwargs), or
            - return a tuple (command_kwargs, broadcast_kwargs) to control both.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, BaseModel]],
    ) -> Callable[..., Coroutine[Any, Any, BaseModel]]:
        @wraps(func)
        async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
            game_state = ctx.deps.game_state
            event_bus = ctx.deps.event_bus
            tool_name = func.__name__
            agent_type = ctx.deps.agent_type

            # Validation: Prevent narrative agent from using combat tools during active combat
            if game_state.combat.is_active and agent_type == AgentType.NARRATIVE:
                # List of tools that should ONLY be used by combat agent during combat
                combat_only_tools = [
                    "roll_dice",  # During combat, only combat agent should roll
                    "update_hp",  # During combat, only combat agent should update HP
                    "update_condition",  # During combat, only combat agent should update conditions
                    "next_turn",  # Combat flow control
                    "end_combat",  # Combat flow control
                    "add_combatant",  # Combat management
                    "remove_combatant",  # Combat management
                ]

                if tool_name in combat_only_tools:
                    error_msg = (
                        f"BLOCKED: Narrative agent attempted to use '{tool_name}' during active combat. "
                        f"This tool should only be used by the combat agent during combat. "
                        f"The narrative agent must STOP after calling start_combat or start_encounter_combat."
                    )
                    logger.error(error_msg)
                    # Also broadcast a policy warning so the user can see policy enforcement
                    try:
                        await event_bus.submit_and_wait(
                            [
                                BroadcastPolicyWarningCommand(
                                    game_id=game_state.game_id,
                                    message="Blocked tool usage during combat",
                                    tool_name=tool_name,
                                    agent_type=agent_type.value,
                                )
                            ]
                        )
                    except Exception:
                        logger.debug("Failed to broadcast blocked-tool system message", exc_info=True)
                    # Return a dummy result to prevent the agent from crashing
                    # but the error will be logged
                    from pydantic import BaseModel as BlockedBaseModel

                    class BlockedToolResult(BlockedBaseModel):
                        type: str = "blocked"
                        message: str
                        tool_name: str

                    return BlockedToolResult(message=error_msg, tool_name=tool_name, type="blocked")

            original_kwargs: dict[str, JSONSerializable] = cast(dict[str, JSONSerializable], dict(kwargs))

            # Optionally transform kwargs for command construction and/or broadcast
            if prepare is not None:
                prepared = prepare(dict(original_kwargs))  # pass a copy to avoid side effects
                if isinstance(prepared, tuple):
                    command_kwargs = prepared[0]
                    broadcast_kwargs: dict[str, JSONSerializable] = prepared[1]
                else:
                    command_kwargs = prepared
                    broadcast_kwargs = original_kwargs
            else:
                command_kwargs = original_kwargs
                broadcast_kwargs = original_kwargs

            # 1. Broadcast tool call
            await event_bus.submit_command(
                BroadcastToolCallCommand(
                    game_id=game_state.game_id,
                    tool_name=tool_name,
                    parameters=broadcast_kwargs,
                ),
            )

            # 2. Persist TOOL_CALL event
            try:
                ctx.deps.event_manager.add_event(
                    game_state=game_state,
                    event_type=GameEventType.TOOL_CALL,
                    tool_name=tool_name,
                    parameters=broadcast_kwargs,
                )
                ctx.deps.save_manager.save_game(game_state)
            except Exception as e:
                # Do not fail tool execution if event persistence fails
                logger.error(
                    f"Failed to persist TOOL_CALL for {tool_name}: {e}",
                    exc_info=True,
                )

            # 3. Execute domain command (use factory if provided)
            if command_factory is not None:
                command = command_factory(ctx, command_kwargs)
            else:
                if command_class is None:
                    raise RuntimeError(
                        "tool_handler requires either command_class or command_factory to be provided",
                    )
                # Pass agent_type to commands that support it
                # Build kwargs with game_id first
                final_kwargs: dict[str, Any] = {"game_id": game_state.game_id}

                # Add agent_type if the command class has this field
                if (
                    hasattr(command_class, "__dataclass_fields__")
                    and "agent_type" in command_class.__dataclass_fields__
                ):
                    final_kwargs["agent_type"] = ctx.deps.agent_type

                # Add the rest of the command kwargs
                final_kwargs.update(command_kwargs)

                command = command_class(**final_kwargs)
            result = await event_bus.execute_command(command)

            # 4. Broadcast tool result and 5. Persist TOOL_RESULT event
            if result:
                # Guard result type before broadcasting and persisting
                # Import here to avoid circular imports
                from app.models.tool_results import ToolResult

                if not isinstance(result, ToolResult):
                    logger.warning(
                        f"Tool '{tool_name}' returned unexpected result type: {type(result)}; "
                        "skipping TOOL_RESULT broadcast/persistence",
                    )
                    return result

                tool_result = result

                await event_bus.submit_command(
                    BroadcastToolResultCommand(
                        game_id=game_state.game_id,
                        tool_name=tool_name,
                        result=tool_result,
                    ),
                )

                try:
                    ctx.deps.event_manager.add_event(
                        game_state=game_state,
                        event_type=GameEventType.TOOL_RESULT,
                        tool_name=tool_name,
                        result=tool_result.model_dump(mode="json"),
                    )
                    ctx.deps.save_manager.save_game(game_state)
                except Exception as e:
                    logger.error(
                        f"Failed to persist TOOL_RESULT for {tool_name}: {e}",
                        exc_info=True,
                    )

                return result

            # No result is a serious error - commands should always return something
            # Use the constructed command type for clearer error without Optional issues
            raise RuntimeError(
                f"Command {type(command).__name__} returned None for tool {tool_name}",
            )

        # Preserve the original function's metadata
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__

        return wrapper

    return decorator
