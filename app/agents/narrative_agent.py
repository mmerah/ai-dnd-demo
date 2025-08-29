"""Agent that handles all narrative D&D gameplay."""

import json
import logging
from collections.abc import AsyncIterable, AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
)

from app.agents.base import BaseAgent
from app.models.ai_response import (
    NarrativeResponse,
    StreamEvent,
    StreamEventType,
    ToolCallEvent,
)
from app.models.dependencies import AgentDependencies
from app.models.game_state import GameState, MessageRole
from app.services.context_service import ContextService
from app.services.dice_service import DiceService
from app.services.event_logger_service import EventLoggerService
from app.services.game_service import GameService
from app.services.message_converter_service import MessageConverterService
from app.services.message_service import message_service
from app.tools import character_tools, dice_tools, inventory_tools, time_tools

logger = logging.getLogger(__name__)

# Type alias for PydanticAI streaming events
PydanticAIEvent = PartStartEvent | PartDeltaEvent | FunctionToolCallEvent | FunctionToolResultEvent


@dataclass
class NarrativeAgent(BaseAgent):
    """Agent that handles all narrative D&D gameplay."""

    agent: Agent[AgentDependencies, str]
    context_service: ContextService
    message_converter: MessageConverterService
    event_logger: EventLoggerService
    event_bus: Any  # EventBus type, using Any to avoid circular import
    # Any types are unavoidable here as tool arguments and results vary by tool
    # Format: (tool_name, args_dict | None, result | None)
    captured_events: list[tuple[str, dict[str, Any] | None, Any | None]] = field(default_factory=list)

    def get_required_tools(self) -> list[Callable[..., Any]]:
        """Return list of tools this agent requires."""
        return [
            # Dice and combat tools
            dice_tools.roll_ability_check,
            dice_tools.roll_saving_throw,
            dice_tools.roll_attack,
            dice_tools.roll_damage,
            dice_tools.roll_initiative,
            # Character management tools
            character_tools.update_hp,
            character_tools.add_condition,
            character_tools.remove_condition,
            character_tools.update_spell_slots,
            # Inventory tools
            inventory_tools.modify_currency,
            inventory_tools.add_item,
            inventory_tools.remove_item,
            # Time management tools
            time_tools.short_rest,
            time_tools.long_rest,
            time_tools.advance_time,
        ]

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[Any],  # PydanticAI's internal event type
    ) -> None:
        """Handle streaming events and log tool calls."""
        game_id = ctx.deps.game_state.game_id
        logger.info("Event stream handler started")

        # Track tool calls by ID to match with results
        tool_calls_by_id: dict[str, str] = {}
        # Clear captured events for this run
        self.captured_events = []

        async for event in event_stream:
            # Only log non-delta events to reduce spam
            if not isinstance(event, PartDeltaEvent):
                logger.info(f"Event received: {type(event).__name__}")
            logger.debug(f"Event details: {event}")

            if isinstance(event, PartStartEvent):
                # Starting a new part (text, tool call, thinking)
                logger.debug(f"PartStartEvent - Part type: {type(event.part).__name__}")
                if hasattr(event.part, "content") and isinstance(event.part, ThinkingPart):
                    content = getattr(event.part, "content", None)
                    if content:
                        self.event_logger.log_thinking(content)
                # Check if it's a tool call part
                if isinstance(event.part, ToolCallPart):
                    logger.info(f"Tool call part detected: {event.part.tool_name}")
                    tool_name = event.part.tool_name
                    tool_call_id = getattr(event.part, "tool_call_id", None)
                    args = event.part.args if hasattr(event.part, "args") else {}

                    # Store tool name by ID for later matching
                    if tool_call_id:
                        tool_calls_by_id[tool_call_id] = tool_name

                    # Skip broadcasting if args are empty or just an empty string
                    # This avoids the duplicate empty tool call
                    should_skip = False
                    if not args or args == "" or args == {}:
                        logger.debug(f"Skipping empty tool call broadcast for {tool_name}")
                        should_skip = True
                    elif isinstance(args, str):
                        # Try to parse args if it's a string (JSON)
                        try:
                            parsed_args = json.loads(args)
                            args = parsed_args
                        except (json.JSONDecodeError, ValueError):
                            # If it's still an empty string after parsing attempt, skip
                            if not args.strip():
                                logger.debug(f"Skipping empty string args for {tool_name}")
                                should_skip = True
                            else:
                                args = {"raw_args": str(args)}
                    elif not isinstance(args, dict):
                        args = {"raw_args": str(args)}

                    if not should_skip:
                        # Ensure args is a dict at this point
                        if not isinstance(args, dict):
                            args = {"raw_args": str(args)}
                        self.event_logger.log_tool_call(tool_name, args)
                        # Save event for later storage
                        self.captured_events.append((tool_name, args, None))
                        # Broadcast tool call event
                        logger.info(f"Broadcasting tool call: {tool_name} with args: {args}")
                        await message_service.send_tool_call(game_id, tool_name, args)

            elif isinstance(event, PartDeltaEvent):
                # Receiving delta updates
                if isinstance(event.delta, ThinkingPartDelta):
                    if event.delta.content_delta:
                        self.event_logger.log_thinking(event.delta.content_delta)

            elif isinstance(event, FunctionToolCallEvent):
                # Alternative: Tool is being called (for compatibility)
                logger.info("FunctionToolCallEvent detected")
                if hasattr(event, "part") and hasattr(event.part, "tool_name"):
                    tool_name = event.part.tool_name
                    tool_call_id = getattr(event.part, "tool_call_id", None)
                    args = getattr(event.part, "args", {})

                    # Store tool name by ID for later matching
                    if tool_call_id:
                        tool_calls_by_id[tool_call_id] = tool_name

                    if not isinstance(args, dict):
                        args = {"raw_args": str(args)}
                    self.event_logger.log_tool_call(tool_name, args)
                    # Broadcast tool call
                    logger.info(f"Broadcasting tool call via FunctionToolCallEvent: {tool_name} with args: {args}")
                    await message_service.send_tool_call(game_id, tool_name, args)

            elif isinstance(event, FunctionToolResultEvent):
                # Tool returned a result
                logger.info("FunctionToolResultEvent detected")
                logger.debug(f"FunctionToolResultEvent details: {event}")

                # Try different ways to get the tool name and result
                tool_name = "unknown"
                result_content = None

                # First try to get tool name from our tracking dictionary
                if hasattr(event, "tool_call_id") and event.tool_call_id in tool_calls_by_id:
                    tool_name = tool_calls_by_id[event.tool_call_id]

                # Get the result content
                if hasattr(event, "result"):
                    result = event.result
                    if hasattr(result, "content"):
                        result_content = str(result.content)
                    else:
                        result_content = str(result)

                if result_content:
                    self.event_logger.log_tool_result(tool_name, result_content)
                    # Save result event
                    self.captured_events.append((tool_name, None, result_content))
                    # Broadcast tool result
                    logger.info(f"Broadcasting tool result: {tool_name} -> {result_content[:100]}")
                    await message_service.send_tool_result(game_id, tool_name, result_content)

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: GameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        # Update event logger with game ID
        self.event_logger.game_id = game_state.game_id

        # Create dependencies
        deps = AgentDependencies(
            game_state=game_state,
            game_service=game_service,
            dice_service=DiceService(),
            event_bus=self.event_bus,
        )

        # Build context
        context = self.context_service.build_context(game_state)

        # Convert conversation history
        message_history = self.message_converter.to_pydantic_messages(game_state.conversation_history)

        # Create the full prompt with context
        full_prompt = f"{context}\n\nPlayer: {prompt}"

        logger.info(f"Processing prompt: {prompt[:100]}...")
        logger.info(f"Stream mode: {stream}")

        try:
            # For MVP, we'll use non-streaming but still capture tool events
            logger.info(f"Starting response generation (stream={stream})")

            # Run the agent with event handler to capture and broadcast tool calls
            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,  # Always enabled to broadcast tool calls
            )

            logger.info(f"Response generated: {result.output[:100]}...")

            # Process commands through event bus
            from app.events.commands.broadcast_commands import BroadcastNarrativeCommand

            all_commands = []

            # Extract commands from tool results
            for tool_name, params, result_data in self.captured_events:
                if result_data and isinstance(result_data, dict) and "commands" in result_data:
                    commands = result_data.get("commands", [])
                    all_commands.extend(commands)

            # Add narrative broadcast commands
            all_commands.append(
                BroadcastNarrativeCommand(game_id=game_state.game_id, content=result.output, is_complete=False)
            )
            all_commands.append(BroadcastNarrativeCommand(game_id=game_state.game_id, content="", is_complete=True))

            # Submit all commands to event bus
            await self.event_bus.submit_commands(all_commands)

            # Wait for processing to complete
            await self.event_bus.wait_for_completion()

            # Extract tool calls from messages if needed
            tool_calls = []
            for msg in result.new_messages():
                if isinstance(msg, ModelResponse):
                    for part in msg.parts:
                        if isinstance(part, ToolCallPart):
                            if isinstance(part.args, dict):
                                tool_calls.append(
                                    ToolCallEvent(
                                        tool_name=part.tool_name,
                                        args=part.args,
                                        tool_call_id=part.tool_call_id,
                                    )
                                )

            # Save conversation
            game_service.add_message(game_state.game_id, MessageRole.PLAYER, prompt)
            game_service.add_message(game_state.game_id, MessageRole.DM, result.output)

            # Save captured game events
            for tool_name, params, result_data in self.captured_events:
                if params is not None:  # Tool call
                    game_service.add_game_event(
                        game_state.game_id,
                        event_type="tool_call",
                        tool_name=tool_name,
                        parameters=params,
                    )
                elif result_data is not None:  # Tool result
                    game_service.add_game_event(
                        game_state.game_id,
                        event_type="tool_result",
                        tool_name=tool_name,
                        result=result_data,
                    )

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(
                    narrative=result.output,
                    tool_calls=tool_calls,
                ),
            )

        except Exception as e:
            self.event_logger.log_error(e)
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e),
                metadata={"error_type": type(e).__name__},
            )
            # Fail fast - re-raise the exception
            raise
