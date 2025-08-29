"""AI Service with PydanticAI integration for D&D 5e DM using native tool system."""

from typing import Dict, Any, Optional, AsyncIterator, List
import asyncio
import logging

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    AgentStreamEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    FinalResultEvent,
    PartDeltaEvent,
    TextPartDelta,
)
from dotenv import load_dotenv

from app.config import get_settings
from app.models.game_state import GameState, MessageRole, Message
from app.models.dependencies import AgentDependencies
from app.services.game_service import GameService
from app.services.dice_service import DiceService
from app.services.scenario_service import ScenarioService
from app.services.message_service import message_service
from app.tools import character_tools, dice_tools, inventory_tools, time_tools

load_dotenv()
logger = logging.getLogger(__name__)


class AIService:
    """Service for AI Dungeon Master interactions using PydanticAI native tools."""
    
    def __init__(self) -> None:
        """
        Initialize AI Service with configuration from settings.
        """
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model_name = settings.openrouter_model
        self.max_retries = settings.max_retries
        self.debug_mode = settings.debug_ai
        
        # OpenRouter uses an OpenAI-compatible API at a different base URL
        provider = OpenRouterProvider(
            api_key=self.api_key
        )
        
        self.model = OpenAIModel(
            self.model_name,
            provider=provider
        )
        
        # Register all tools and initialize the agent
        self._register_tools()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the D&D DM."""
        return """You are an expert Dungeon Master for D&D 5th Edition, creating immersive and engaging adventures.

## Your Role
You are the narrator, rules arbiter, and controller of all NPCs and monsters. Your goal is to create a fun, challenging, and memorable experience for the player.

## Narrative Style
- Use second person ("You see..." not "The character sees...")
- Be descriptive and atmospheric, including sensory details
- Keep responses concise but evocative (2-4 paragraphs typically)
- React dynamically to player choices
- Balance description with action

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
    
    def _register_tools(self) -> None:
        """Register all D&D game tools with the agent."""
        # Initialize the agent first
        self.agent = Agent(
            model=self.model,
            deps_type=AgentDependencies,
            system_prompt=self._get_system_prompt(),
            retries=self.max_retries
        )
        
        # Register tools using the agent.tool decorator
        # This ensures proper tool registration with PydanticAI
        
        # Dice and combat tools
        self.agent.tool(dice_tools.roll_ability_check)
        self.agent.tool(dice_tools.roll_saving_throw)
        self.agent.tool(dice_tools.roll_attack)
        self.agent.tool(dice_tools.roll_damage)
        self.agent.tool(dice_tools.roll_initiative)
        
        # Character management tools
        self.agent.tool(character_tools.update_hp)
        self.agent.tool(character_tools.add_condition)
        self.agent.tool(character_tools.remove_condition)
        self.agent.tool(character_tools.update_spell_slots)
        
        # Inventory tools
        self.agent.tool(inventory_tools.modify_currency)
        self.agent.tool(inventory_tools.add_item)
        self.agent.tool(inventory_tools.remove_item)
        
        # Time management tools
        self.agent.tool(time_tools.short_rest)
        self.agent.tool(time_tools.long_rest)
        self.agent.tool(time_tools.advance_time)
        
        logger.info(f"Registered 16 tools with the agent successfully")
    
    def _build_context_string(self, game_state: GameState) -> str:
        """Build context string from game state (excluding conversation history)."""
        context_parts = []
        
        # Add scenario context if available
        if game_state.scenario_id and game_state.current_location_id:
            scenario_service = ScenarioService()
            scenario = scenario_service.get_scenario(game_state.scenario_id)
            if scenario:
                scenario_context = scenario_service.get_scenario_context_for_ai(
                    scenario, 
                    game_state.current_location_id
                )
                context_parts.append(scenario_context)
        
        # Add current game state
        char = game_state.character
        context_parts.append(f"""Current State:
- Character: {char.name} ({char.race} {char.class_name} Level {char.level})
- HP: {char.hit_points.current}/{char.hit_points.maximum}, AC: {char.armor_class}
- Location: {game_state.location}
- Time: Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}""")
        
        if game_state.npcs:
            npc_lines = [f"  - {npc.name}: HP {npc.hit_points.current}/{npc.hit_points.maximum}, AC {npc.armor_class}" for npc in game_state.npcs]
            context_parts.append("NPCs Present:\n" + "\n".join(npc_lines))
        
        if game_state.combat:
            current_turn = game_state.combat.get_current_turn()
            turn_info = f", Turn: {current_turn.name}" if current_turn else ""
            context_parts.append(f"Combat: Round {game_state.combat.round_number}{turn_info}")
        
        # Don't include conversation history here - it will be handled via message_history
        
        return "\n\n".join(context_parts)
    
    def _convert_messages_to_pydantic_ai(self, messages: List[Message]) -> List[ModelMessage]:
        """Convert our internal Message format to PydanticAI's ModelMessage format."""
        pydantic_messages: List[ModelMessage] = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # System messages become ModelRequest with SystemPromptPart
                pydantic_messages.append(
                    ModelRequest(parts=[SystemPromptPart(content=msg.content)])
                )
            elif msg.role == MessageRole.PLAYER:
                # Player messages become ModelRequest with UserPromptPart
                pydantic_messages.append(
                    ModelRequest(parts=[UserPromptPart(content=msg.content)])
                )
            elif msg.role == MessageRole.DM:
                # DM messages become ModelResponse with TextPart
                pydantic_messages.append(
                    ModelResponse(parts=[TextPart(content=msg.content)])
                )
        
        return pydantic_messages
    
    async def _extract_and_broadcast_tool_events(
        self, 
        game_id: str, 
        messages: List[ModelMessage]
    ) -> None:
        """Extract tool calls and results from messages and broadcast them."""
        for i, msg in enumerate(messages):
            if isinstance(msg, ModelResponse):
                # Check for tool calls in the response
                for part in msg.parts:
                    if isinstance(part, ToolCallPart):
                        logger.debug(f"Found tool call: {part.tool_name} with args: {part.args}")
                        # Broadcast tool call event
                        await message_service.send_tool_call(
                            game_id,
                            part.tool_name,
                            part.args
                        )
                        
                        # Look for the corresponding tool result in next message
                        if i + 1 < len(messages):
                            next_msg = messages[i + 1]
                            if isinstance(next_msg, ModelRequest):
                                for next_part in next_msg.parts:
                                    if isinstance(next_part, ToolReturnPart) and next_part.tool_name == part.tool_name:
                                        logger.debug(f"Found tool result for {part.tool_name}: {next_part.content}")
                                        # Broadcast tool result event
                                        await message_service.send_tool_result(
                                            game_id,
                                            part.tool_name,
                                            next_part.content
                                        )
    
    async def _handle_stream_events(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterator[AgentStreamEvent],
        game_id: str
    ) -> None:
        """Handle streaming events and broadcast tool calls in real-time."""
        async for event in event_stream:
            if isinstance(event, FunctionToolCallEvent):
                # Broadcast tool call in real-time
                logger.debug(f"Real-time tool call: {event.part.tool_name} with args: {event.part.args}")
                await message_service.send_tool_call(
                    game_id,
                    event.part.tool_name,
                    event.part.args
                )
            elif isinstance(event, FunctionToolResultEvent):
                # Broadcast tool result in real-time
                logger.debug(f"Real-time tool result for {event.tool_call_id}: {event.result.content}")
                # Note: FunctionToolResultEvent has tool_call_id but not tool_name directly
                await message_service.send_tool_result(
                    game_id,
                    event.tool_call_id,
                    event.result.content
                )
            elif isinstance(event, PartDeltaEvent):
                # Handle text streaming - but we'll use stream_text() for actual text
                if isinstance(event.part_delta, TextPartDelta):
                    logger.debug(f"Text delta received: {len(event.part_delta.content_delta) if event.part_delta.content_delta else 0} chars")
            elif isinstance(event, FinalResultEvent):
                # Final result event - narrative is about to start
                logger.debug(f"Final result starting for game {game_id}")
                # Signal narrative start when we get the final result
                await message_service.send_narrative(game_id, "", is_complete=False)
    
    async def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        game_service: GameService,
        stream: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
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
        deps = AgentDependencies(
            game_state=game_state,
            game_service=game_service,
            dice_service=DiceService()
        )
        
        # Build context (without conversation history)
        context = self._build_context_string(game_state)
        
        # Convert conversation history to PydanticAI format
        message_history = self._convert_messages_to_pydantic_ai(game_state.conversation_history)
        
        # Create the user message with context
        full_user_message = f"{context}\n\nPlayer: {user_message}"
        
        logger.info(f"Generating response for: {user_message[:100]}")
        
        try:
            if stream:
                # Use streaming with event handler for real-time tool tracking
                narrative = ""
                try:
                    # Create event handler for tool tracking
                    async def event_handler(ctx: RunContext[AgentDependencies], events: AsyncIterator[AgentStreamEvent]):
                        await self._handle_stream_events(ctx, events, game_state.game_id)
                    
                    # Run with streaming and event handling
                    async with self.agent.run_stream(
                        full_user_message,
                        deps=deps,
                        message_history=message_history,
                        event_stream_handler=event_handler
                    ) as run_stream:
                        # Stream the narrative text using delta mode for real chunks
                        collected_text = ""
                        async for text_chunk in run_stream.stream_text(delta=True):
                            collected_text += text_chunk
                            # Send chunks for UI streaming effect
                            yield {
                                "type": "narrative_chunk",
                                "content": text_chunk
                            }
                            await message_service.send_narrative(game_state.game_id, text_chunk, is_chunk=True)
                            await asyncio.sleep(0.01)  # Small delay for streaming effect
                        
                        narrative = collected_text
                        
                        # Save conversation (only save DM message if we have content)
                        game_service.add_message(game_state.game_id, MessageRole.PLAYER, user_message)
                        if narrative:
                            game_service.add_message(game_state.game_id, MessageRole.DM, narrative)
                        else:
                            logger.warning(f"No narrative content generated for game {game_state.game_id}")
                        
                        # Signal end of narrative
                        await message_service.send_narrative(game_state.game_id, "", is_complete=True)
                        
                        yield {
                            "type": "complete",
                            "narrative": narrative if narrative else "I couldn't generate a response. Please try again."
                        }
                except Exception as stream_error:
                    logger.error(f"Streaming error: {stream_error}", exc_info=True)
                    logger.error(f"Error type: {type(stream_error).__name__}")
                    logger.error(f"Model: {self.model_name}, API Key present: {bool(self.api_key)}")
                    # Provide a fallback narrative
                    fallback_narrative = "I encountered an error while processing your request. Please try again."
                    yield {
                        "type": "error",
                        "message": f"Streaming failed: {str(stream_error)}",
                        "narrative": fallback_narrative
                    }
            else:
                # Non-streaming response
                run_result = await self.agent.run(
                    full_user_message, 
                    deps=deps,
                    message_history=message_history
                )
                narrative = run_result.output
                
                # Extract and broadcast tool events
                new_messages = run_result.new_messages()
                await self._extract_and_broadcast_tool_events(game_state.game_id, new_messages)
                
                # Save conversation
                game_service.add_message(game_state.game_id, MessageRole.PLAYER, user_message)
                game_service.add_message(game_state.game_id, MessageRole.DM, narrative)
                
                yield {
                    "type": "complete",
                    "narrative": narrative
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"Failed to generate response: {str(e)}"
            }