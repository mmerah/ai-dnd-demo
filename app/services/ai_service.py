"""Refactored AI Service with SOLID principles and modern pydantic-ai patterns."""

import logging
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.settings import ModelSettings

from app.config import get_settings
from app.models.ai_response import (
    NarrativeResponse,
    StreamEvent,
    StreamEventType,
    ToolCallEvent,
)
from app.models.dependencies import AgentDependencies
from app.models.game_state import GameState, Message, MessageRole
from app.services.dice_service import DiceService
from app.services.game_service import GameService
from app.services.message_service import message_service
from app.services.scenario_service import ScenarioService
from app.tools import character_tools, dice_tools, inventory_tools, time_tools

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents."""

    NARRATIVE = "narrative"
    COMBAT = "combat"
    SUMMARIZER = "summarizer"


class BaseAgent:
    """Base class for all specialized agents."""

    def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: GameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        raise NotImplementedError("Subclasses must implement process method")


@dataclass
class EventLogger:
    """Handles logging of agent events to console."""

    game_id: str
    debug: bool = False

    def log_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        """Log a tool call event."""
        logger.info(f"[TOOL_CALL] {tool_name}: {args}")

    def log_tool_result(self, tool_name: str, result: str) -> None:
        """Log a tool result event."""
        logger.info(f"[TOOL_RESULT] {tool_name}: {result}")

    def log_thinking(self, content: str) -> None:
        """Log thinking content."""
        if self.debug:
            logger.debug(f"[THINKING] {content}")

    def log_error(self, error: Exception) -> None:
        """Log an error with full details."""
        logger.error(f"[ERROR] {type(error).__name__}: {str(error)}", exc_info=True)


class MessageConverter:
    """Handles conversion between internal and pydantic-ai message formats."""

    @staticmethod
    def to_pydantic_messages(messages: list[Message]) -> list[ModelMessage]:
        """Convert internal Message format to PydanticAI's ModelMessage format."""
        pydantic_messages: list[ModelMessage] = []

        for msg in messages:
            if msg.role == MessageRole.PLAYER:
                pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            elif msg.role == MessageRole.DM:
                pydantic_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        return pydantic_messages


class ContextBuilder:
    """Builds context strings for AI prompts."""

    def __init__(self, scenario_service: ScenarioService):
        self.scenario_service = scenario_service

    def build_context(self, game_state: GameState) -> str:
        """Build context string from game state."""
        context_parts = []

        # Add scenario context if available
        if game_state.scenario_id and game_state.current_location_id:
            scenario = self.scenario_service.get_scenario(game_state.scenario_id)
            if scenario:
                scenario_context = self.scenario_service.get_scenario_context_for_ai(
                    scenario, game_state.current_location_id
                )
                context_parts.append(scenario_context)

        # Add current game state
        char = game_state.character
        context_parts.append(
            f"""Current State:
- Character: {char.name} ({char.race} {char.class_name} Level {char.level})
- HP: {char.hit_points.current}/{char.hit_points.maximum}, AC: {char.armor_class}
- Location: {game_state.location}
- Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"""
        )

        if game_state.npcs:
            npc_lines = [
                f"  - {npc.name}: HP {npc.hit_points.current}/{npc.hit_points.maximum}, AC {npc.armor_class}"
                for npc in game_state.npcs
            ]
            context_parts.append("NPCs Present:\n" + "\n".join(npc_lines))

        if game_state.combat:
            current_turn = game_state.combat.get_current_turn()
            turn_info = f", Turn: {current_turn.name}" if current_turn else ""
            context_parts.append(f"Combat: Round {game_state.combat.round_number}{turn_info}")

        return "\n\n".join(context_parts)


@dataclass
class NarrativeAgent(BaseAgent):
    """Agent that handles all narrative D&D gameplay."""

    agent: Agent[AgentDependencies, str]
    context_builder: ContextBuilder
    message_converter: MessageConverter
    event_logger: EventLogger
    captured_events: list[tuple[str, dict[str, Any] | None, Any | None]] = field(default_factory=list)

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[Any],
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
                            import json

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
                elif hasattr(event, "tool_name"):
                    tool_name = event.tool_name

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
        )

        # Build context
        context = self.context_builder.build_context(game_state)

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

            # For MVP, send the complete narrative at once
            # Frontend can still display it nicely
            await message_service.send_narrative(game_state.game_id, result.output, is_chunk=False)
            await message_service.send_narrative(game_state.game_id, "", is_complete=True)

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


class AgentFactory:
    """Factory for creating specialized agents."""

    # Static system prompt - for caching benefits
    NARRATIVE_SYSTEM_PROMPT = """You are an expert Dungeon Master for D&D 5th Edition, creating immersive and engaging adventures.

## Your Role
You are the narrator, rules arbiter, and controller of all NPCs and monsters. Your goal is to create a fun, challenging, and memorable experience for the player.

## Narrative Style
- Use second person ("You see..." not "The character sees...")
- Be descriptive and atmospheric, including sensory details
- Be engaging to the player
- Keep responses evocative (2-4 paragraphs)
- React dynamically to player choices
- Balance description with action
- Use markdown formatting for better readability:
  - **Bold** for emphasis and important information
  - *Italics* for thoughts, whispers, or subtle details
  - ### Headers for scene changes or important moments
  - Lists for multiple options or items

## D&D 5e Core Mechanics
- **Ability Checks**: d20 + ability modifier + proficiency (if proficient) vs DC
- **Saving Throws**: d20 + save modifier vs DC
- **Attack Rolls**: d20 + attack bonus vs AC
- **Damage**: Roll specified dice and apply
- **Advantage/Disadvantage**: Roll twice, take higher/lower
- **DCs**: Easy (10), Medium (15), Hard (20), Very Hard (25)

## Tool Usage Guidelines
You have access to game tools that handle mechanics. Use them naturally when:
- Combat occurs (attacks, damage, initiative)
- Skill checks are needed (ability checks, saves)
- State changes (HP, conditions, inventory)
- Time passes (rests, travel)
- Resources change (spells, currency)

Let the tools handle the mechanical resolution while you focus on narrative.

## Combat Flow
1. Call for initiative when combat starts
2. Describe actions cinematically
3. Resolve attacks and damage through tools
4. Track conditions and HP changes
5. End combat when appropriate

## Important Reminders
- You are the final authority on rules and outcomes
- Keep the game moving forward
- Challenge the player appropriately for their level
- NPCs should have distinct personalities
- Reward clever thinking and good roleplay

The current game state and character information will be provided with each interaction."""

    @classmethod
    def _register_tools(cls, agent: Agent[AgentDependencies, str]) -> None:
        """Register all D&D game tools with the agent."""
        # Dice and combat tools
        agent.tool(dice_tools.roll_ability_check)
        agent.tool(dice_tools.roll_saving_throw)
        agent.tool(dice_tools.roll_attack)
        agent.tool(dice_tools.roll_damage)
        agent.tool(dice_tools.roll_initiative)

        # Character management tools
        agent.tool(character_tools.update_hp)
        agent.tool(character_tools.add_condition)
        agent.tool(character_tools.remove_condition)
        agent.tool(character_tools.update_spell_slots)

        # Inventory tools
        agent.tool(inventory_tools.modify_currency)
        agent.tool(inventory_tools.add_item)
        agent.tool(inventory_tools.remove_item)

        # Time management tools
        agent.tool(time_tools.short_rest)
        agent.tool(time_tools.long_rest)
        agent.tool(time_tools.advance_time)

        logger.info("Registered 16 tools with the agent")

    @classmethod
    def create_agent(cls, agent_type: AgentType, debug: bool = False) -> BaseAgent:
        """Create a specialized agent based on type."""
        settings = get_settings()

        # Create model with OpenRouter via OpenAI provider
        # OpenRouter requires special headers for proper operation
        import httpx
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        headers = {
            "HTTP-Referer": "http://localhost:8123",  # Required by OpenRouter
            "X-Title": "D&D AI Dungeon Master",  # Optional but recommended
        }

        http_client = httpx.AsyncClient(headers=headers)

        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            http_client=http_client,
        )
        model = OpenAIModel(
            settings.openrouter_model,  # "openai/gpt-oss-120b"
            provider=provider,
        )

        # Model settings for parallel tool calls and thinking
        model_settings = ModelSettings(temperature=0.7, max_tokens=4096, parallel_tool_calls=True)

        logger.info(
            f"Model settings: temperature={model_settings.get('temperature')}, max_tokens={model_settings.get('max_tokens')}"
        )

        # Note: OpenAI thinking settings would be applied here if the model supports it
        # For now, we'll use standard settings as openai/gpt-oss-120b may not support thinking parts

        if agent_type == AgentType.NARRATIVE:
            # Create the narrative agent
            agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=cls.NARRATIVE_SYSTEM_PROMPT,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            # Register tools
            cls._register_tools(agent)

            # Create supporting services
            context_builder = ContextBuilder(ScenarioService())
            message_converter = MessageConverter()
            event_logger = EventLogger(game_id="", debug=debug)

            return NarrativeAgent(
                agent=agent,
                context_builder=context_builder,
                message_converter=message_converter,
                event_logger=event_logger,
            )

        elif agent_type == AgentType.COMBAT:
            # Future: Specialized combat agent
            raise NotImplementedError("Combat agent not yet implemented")

        elif agent_type == AgentType.SUMMARIZER:
            # Future: Specialized summarizer agent
            raise NotImplementedError("Summarizer agent not yet implemented")

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")


class AIService:
    """Main AI Service that coordinates specialized agents."""

    def __init__(self) -> None:
        """Initialize AI Service."""
        settings = get_settings()
        self.debug_mode = settings.debug_ai

        # Create the narrative agent for MVP
        self.narrative_agent = AgentFactory.create_agent(AgentType.NARRATIVE, debug=self.debug_mode)

    async def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        game_service: GameService,
        stream: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Generate AI response with streaming support.

        Args:
            user_message: The player's input
            game_state: Current game state
            game_service: Game service instance
            stream: Whether to stream the response

        Yields:
            Dict with response chunks or complete response
        """
        logger.info(f"AIService.generate_response called with stream={stream}")
        try:
            # Process through the narrative agent
            event_count = 0
            async for event in self.narrative_agent.process(user_message, game_state, game_service, stream):
                event_count += 1
                logger.debug(f"AIService received event {event_count}: type={event.type}")
                # Convert StreamEvent to the expected format
                if event.type == StreamEventType.NARRATIVE_CHUNK:
                    logger.debug(f"Yielding narrative_chunk: '{event.content[:30]}...'")
                    yield {"type": "narrative_chunk", "content": event.content}
                elif event.type == StreamEventType.COMPLETE:
                    response: NarrativeResponse = event.content
                    logger.info(
                        f"Yielding complete event with narrative length: {len(response.narrative) if response.narrative else 0}"
                    )
                    yield {
                        "type": "complete",
                        "narrative": response.narrative
                        if response.narrative
                        else "I couldn't generate a response. Please try again.",
                    }
                elif event.type == StreamEventType.ERROR:
                    logger.error(f"Yielding error event: {event.content}")
                    yield {
                        "type": "error",
                        "message": f"Failed to generate response: {event.content}",
                    }
            logger.info(f"AIService.generate_response completed. Total events: {event_count}")
        except Exception as e:
            logger.error(f"Error in generate_response: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"Failed to generate response: {str(e)}",
            }
            # Fail fast
            raise
