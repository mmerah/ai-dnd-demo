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
)
from app.models.tool_results import ToolErrorResult

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

            if agent_type == AgentType.NPC:
                npc_allowed_tools = {
                    "start_quest",
                    "complete_objective",
                    "complete_quest",
                    "modify_inventory",
                    "update_location_state",
                    "discover_secret",
                    "move_npc_to_location",
                }

                if tool_name not in npc_allowed_tools:
                    error_msg = (
                        f"BLOCKED: NPC agent attempted to use '{tool_name}'. "
                        "NPC agents may only use quest, inventory, or safe location tools."
                    )
                    logger.error(error_msg)
                    try:
                        await event_bus.submit_and_wait(
                            [
                                BroadcastPolicyWarningCommand(
                                    game_id=game_state.game_id,
                                    message="Blocked tool usage for NPC agent",
                                    tool_name=tool_name,
                                    agent_type=agent_type.value,
                                )
                            ]
                        )
                    except Exception:
                        logger.debug("Failed to broadcast blocked-tool system message", exc_info=True)

                    class BlockedToolResultNPC(BaseModel):
                        type: str = "blocked"
                        message: str
                        tool_name: str

                    return BlockedToolResultNPC(message=error_msg, tool_name=tool_name)

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

            # Build command (use factory if provided)
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

            # Execute via common ActionService to ensure DRY handling
            try:
                result = await ctx.deps.action_service.execute_command_as_action(
                    tool_name=tool_name,
                    command=command,
                    game_state=game_state,
                    broadcast_parameters=broadcast_kwargs,
                )
            except ValueError as e:
                # Return structured error that AI can understand and potentially correct
                logger.warning(f"Tool {tool_name} encountered error: {str(e)}")

                # Try to provide helpful suggestions based on common errors
                suggestion = None
                error_msg = str(e).lower()
                if "not found" in error_msg:
                    suggestion = "Check the ID or name is correct. You may need to list available options first."
                elif "cannot travel" in error_msg or "valid destinations" in error_msg:
                    suggestion = "Check the available connections from the current location."
                elif "empty" in error_msg:
                    suggestion = "Provide a value for the required parameter."
                elif "invalid" in error_msg:
                    suggestion = "Check that the provided value is in the correct format or from the allowed options."

                return ToolErrorResult(
                    error=str(e),
                    tool_name=tool_name,
                    suggestion=suggestion,
                )

            return result

        # Preserve the original function's metadata
        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__

        return wrapper

    return decorator
