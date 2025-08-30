"""Agent that handles all narrative D&D gameplay."""

import json
import logging
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from pydantic import BaseModel
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

from app.agents.base import BaseAgent, ToolFunction
from app.agents.dependencies import AgentDependencies
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services import IDataService, IGameService, IScenarioService
from app.models.ai_response import (
    CapturedToolEvent,
    NarrativeResponse,
    StreamEvent,
    StreamEventType,
    ToolCallEvent,
)
from app.models.game_state import GameState, MessageRole
from app.models.tool_results import ToolResult
from app.services.context_service import ContextService
from app.services.event_logger_service import EventLoggerService
from app.services.message_converter_service import MessageConverterService
from app.services.message_metadata_service import MessageMetadataService
from app.tools import (
    character_tools,
    combat_tools,
    dice_tools,
    inventory_tools,
    location_tools,
    quest_tools,
    time_tools,
)

logger = logging.getLogger(__name__)

# Type alias for PydanticAI streaming events
PydanticAIEvent: TypeAlias = PartStartEvent | PartDeltaEvent | FunctionToolCallEvent | FunctionToolResultEvent


@dataclass
class NarrativeAgent(BaseAgent):
    """Agent that handles all narrative D&D gameplay."""

    agent: Agent[AgentDependencies, str]
    context_service: ContextService
    message_converter: MessageConverterService
    event_logger: EventLoggerService
    metadata_service: MessageMetadataService
    event_bus: IEventBus
    scenario_service: IScenarioService
    data_service: IDataService
    captured_events: list[CapturedToolEvent] = field(default_factory=list)

    def get_required_tools(self) -> list[ToolFunction]:
        """Return list of tools this agent requires."""
        return [
            # Dice and combat tools
            dice_tools.roll_dice,
            # Character management tools
            character_tools.update_hp,
            character_tools.update_condition,
            character_tools.update_spell_slots,
            # Inventory tools
            inventory_tools.modify_currency,
            inventory_tools.modify_inventory,
            # Time management tools
            time_tools.short_rest,
            time_tools.long_rest,
            time_tools.advance_time,
            # Location and navigation tools
            location_tools.change_location,
            location_tools.discover_secret,
            location_tools.update_location_state,
            # Combat management tools
            combat_tools.start_combat,
            combat_tools.trigger_scenario_encounter,
            combat_tools.spawn_monsters,
            # Quest management tools
            quest_tools.start_quest,
            quest_tools.complete_objective,
            quest_tools.complete_quest,
            quest_tools.progress_act,
        ]

    async def event_stream_handler(
        self,
        _ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[Any],  # PydanticAI's internal event type
    ) -> None:
        """Handle streaming events and log tool calls."""
        logger.debug("Event stream handler started")

        # Track tool calls by ID to match with results
        tool_calls_by_id: dict[str, str] = {}
        # Track which tool calls we've already processed to avoid duplicates
        processed_tool_calls: set[str] = set()
        # DO NOT clear captured_events here - it gets called multiple times!

        async for event in event_stream:
            # Skip logging delta events to reduce spam
            if not isinstance(event, PartDeltaEvent):
                logger.debug(f"Event received: {type(event).__name__} - details: {event}")

            if isinstance(event, PartStartEvent):
                # Starting a new part (text, tool call, thinking)
                logger.debug(f"PartStartEvent - Part type: {type(event.part).__name__}")
                if hasattr(event.part, "content") and isinstance(event.part, ThinkingPart):
                    content = getattr(event.part, "content", None)
                    if content:
                        self.event_logger.log_thinking(content)
                # Check if it's a tool call part
                if isinstance(event.part, ToolCallPart):
                    tool_name = event.part.tool_name
                    tool_call_id = getattr(event.part, "tool_call_id", None)
                    args = event.part.args if hasattr(event.part, "args") else {}

                    # Store tool name by ID for later matching
                    if tool_call_id:
                        # Check if we've already processed this tool call
                        if tool_call_id in processed_tool_calls:
                            logger.debug(f"Skipping duplicate tool call {tool_call_id} for {tool_name}")
                            continue
                        processed_tool_calls.add(tool_call_id)
                        tool_calls_by_id[tool_call_id] = tool_name

                    # Skip broadcasting if args are empty or just an empty string
                    # This avoids the duplicate empty tool call
                    should_skip = False
                    if not args or args == "" or args == {}:
                        logger.debug(f"Skipping empty tool call broadcast for {tool_name}")
                        should_skip = True
                    elif isinstance(args, str):
                        # Try to parse args if it's a string (JSON)
                        raw_args_str = args.strip()
                        if not raw_args_str:
                            logger.debug(f"Skipping empty string args for {tool_name}")
                            should_skip = True
                        else:
                            try:
                                parsed_args = json.loads(raw_args_str)
                                args = parsed_args
                            except (json.JSONDecodeError, ValueError):
                                args = {"raw_args": raw_args_str}
                    else:
                        # For any other type, convert to string
                        args = {"raw_args": str(args)}

                    if not should_skip:
                        # Ensure args is a dict at this point
                        if not isinstance(args, dict):
                            args = {"raw_args": str(args)}
                        self.event_logger.log_tool_call(tool_name, args)
                        # Save event for later storage
                        self.captured_events.append(CapturedToolEvent(tool_name=tool_name, parameters=args))
                        # Don't broadcast here - tools broadcast themselves via event bus
                        logger.debug(f"Tool call detected: {tool_name} with args: {args}")

            elif isinstance(event, PartDeltaEvent):
                # Receiving delta updates - only process thinking deltas
                if isinstance(event.delta, ThinkingPartDelta) and event.delta.content_delta:
                    self.event_logger.log_thinking(event.delta.content_delta)
                # Skip logging text deltas to prevent spam

            elif isinstance(event, FunctionToolCallEvent):
                # Alternative: Tool is being called (for compatibility)
                logger.debug("FunctionToolCallEvent detected")
                if hasattr(event, "part") and hasattr(event.part, "tool_name"):
                    tool_name = event.part.tool_name
                    tool_call_id = getattr(event.part, "tool_call_id", None)
                    args = getattr(event.part, "args", {})

                    # Store tool name by ID for later matching
                    if tool_call_id:
                        # Check if we've already processed this tool call
                        if tool_call_id in processed_tool_calls:
                            logger.debug(
                                f"Skipping duplicate FunctionToolCallEvent for {tool_name} (already processed)",
                            )
                            continue
                        processed_tool_calls.add(tool_call_id)
                        tool_calls_by_id[tool_call_id] = tool_name

                    if not isinstance(args, dict):
                        args = {"raw_args": str(args)}
                    self.event_logger.log_tool_call(tool_name, args)
                    # Save event for later storage
                    self.captured_events.append(CapturedToolEvent(tool_name=tool_name, parameters=args))
                    # Don't broadcast here - tools broadcast themselves via event bus
                    logger.debug(f"Tool call detected via FunctionToolCallEvent: {tool_name} with args: {args}")

            elif isinstance(event, FunctionToolResultEvent):
                # Tool returned a result
                logger.debug(f"FunctionToolResultEvent detected - details: {event}")

                # Try different ways to get the tool name and result
                tool_name = "unknown"

                # First try to get tool name from our tracking dictionary
                if hasattr(event, "tool_call_id") and event.tool_call_id in tool_calls_by_id:
                    tool_name = tool_calls_by_id[event.tool_call_id]

                # Get the result content
                if hasattr(event, "result"):
                    result = event.result

                    # For logging, use string representation
                    result_str = str(result.content) if hasattr(result, "content") else str(result)
                    self.event_logger.log_tool_result(tool_name, result_str)

                    # Find the corresponding tool call event and update it with the result
                    for captured_event in reversed(self.captured_events):
                        if captured_event.tool_name == tool_name and captured_event.result is None:
                            # The result from the handler is already a typed ToolResult model
                            # We need to convert the raw result to the appropriate ToolResult
                            if hasattr(result, "content") and hasattr(result.content, "model_dump"):
                                # The content is already a BaseModel/ToolResult, use it directly
                                if isinstance(result.content, BaseModel):
                                    # We can only assign if it's actually a ToolResult subtype
                                    # For now, we'll just log if we can't match it
                                    try:
                                        # This is a bit of a hack but works for our case
                                        captured_event.result = result.content  # type: ignore[assignment]
                                    except Exception:
                                        logger.warning(f"Could not assign result for tool {tool_name}")
                            else:
                                # For now, log that we couldn't match the result to a typed model
                                logger.warning(f"Could not type result for tool {tool_name}")
                            break

                    # Don't broadcast here - tools broadcast results via event bus
                    logger.debug(f"Tool result detected: {tool_name} -> {result_str[:100]}")

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        # Update event logger with game ID
        self.event_logger.game_id = game_state.game_id

        # Create dependencies
        deps = AgentDependencies(
            game_state=game_state,
            game_service=game_service,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            data_service=self.data_service,
        )

        # Build context
        context = self.context_service.build_context(game_state)

        # Convert conversation history - filter to only narrative agent messages
        message_history = self.message_converter.to_pydantic_messages(
            game_state.conversation_history,
            agent_type="narrative",
        )

        # Create the full prompt with context
        full_prompt = f"{context}\n\nPlayer: {prompt}"

        logger.debug(f"Processing prompt: {prompt[:100]}... (stream={stream})")

        try:
            # Clear captured events at the start of processing
            self.captured_events = []

            # For MVP, we'll use non-streaming but still capture tool events
            logger.debug(f"Starting response generation (stream={stream})")

            # Run the agent with event handler to capture and broadcast tool calls
            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,  # Always enabled to broadcast tool calls
            )

            logger.debug(f"Response generated: {result.output[:100]}...")

            all_commands = []

            # Extract commands from tool results
            for event in self.captured_events:
                if event.result and hasattr(event.result, "model_dump"):
                    result_data = event.result.model_dump(mode="json")
                    if isinstance(result_data, dict) and "commands" in result_data:
                        commands = result_data.get("commands", [])
                        all_commands.extend(commands)

            # Add narrative broadcast commands
            all_commands.append(
                BroadcastNarrativeCommand(game_id=game_state.game_id, content=result.output, is_complete=False),
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
                        if isinstance(part, ToolCallPart) and isinstance(part.args, dict):
                            tool_calls.append(
                                ToolCallEvent(
                                    tool_name=part.tool_name,
                                    args=part.args,
                                    tool_call_id=part.tool_call_id,
                                ),
                            )

            # Extract metadata for messages
            player_location = self.metadata_service.get_current_location(game_state)
            player_npcs = self.metadata_service.extract_npc_mentions(prompt, game_state.npcs)
            dm_npcs = self.metadata_service.extract_npc_mentions(result.output, game_state.npcs)
            combat_round = self.metadata_service.get_combat_round(game_state)

            # Save conversation with metadata
            game_service.add_message(
                game_state.game_id,
                MessageRole.PLAYER,
                prompt,
                agent_type="narrative",
                location=player_location,
                npcs_mentioned=player_npcs,
                combat_round=combat_round,
            )
            game_service.add_message(
                game_state.game_id,
                MessageRole.DM,
                result.output,
                agent_type="narrative",
                location=player_location,
                npcs_mentioned=dm_npcs,
                combat_round=combat_round,
            )

            # Save captured game events
            logger.debug(f"Saving {len(self.captured_events)} captured events to game state")
            for event in self.captured_events:
                logger.debug(
                    f"Processing event: tool={event.tool_name}, has_params={event.parameters is not None}, has_result={event.result is not None}",
                )
                if event.parameters is not None:  # Tool call
                    logger.debug(f"Adding tool_call event for {event.tool_name}")
                    game_service.add_game_event(
                        game_state.game_id,
                        event_type="tool_call",
                        tool_name=event.tool_name,
                        parameters=event.parameters,
                    )
                if event.result is not None:  # Tool result
                    logger.debug(f"Adding tool_result event for {event.tool_name}")
                    # event.result is a ToolResult which is a BaseModel
                    result_data = event.result.model_dump(mode="json")
                    game_service.add_game_event(
                        game_state.game_id,
                        event_type="tool_result",
                        tool_name=event.tool_name,
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
