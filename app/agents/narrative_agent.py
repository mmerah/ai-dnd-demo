"""Agent that handles all narrative D&D gameplay."""

import logging
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelResponse, ToolCallPart

from app.agents.base import BaseAgent, ToolFunction
from app.agents.dependencies import AgentDependencies
from app.agents.event_handlers import EventStreamProcessor, ToolEventHandler
from app.agents.event_handlers.base import EventContext
from app.agents.event_handlers.thinking_handler import ThinkingHandler
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IGameService,
    IItemRepository,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.models.ai_response import (
    NarrativeResponse,
    StreamEvent,
    StreamEventType,
    ToolCallEvent,
)
from app.models.game_state import GameState, MessageRole
from app.models.npc import NPCSheet
from app.services.ai.context_service import ContextService
from app.services.ai.event_logger_service import EventLoggerService
from app.services.ai.message_converter_service import MessageConverterService
from app.services.ai.message_metadata_service import MessageMetadataService
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
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
    event_processor: EventStreamProcessor | None = None

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

    def _get_event_processor(self) -> EventStreamProcessor:
        """Get or create the event processor."""
        if self.event_processor is None:
            # Create a new context and processor
            context = EventContext(game_id="")
            self.event_processor = EventStreamProcessor(context)

            # Register handlers
            tool_handler = ToolEventHandler(self.event_logger)
            for handler in tool_handler.get_handlers():
                self.event_processor.register_handler(handler)

            thinking_handler = ThinkingHandler(self.event_logger)
            self.event_processor.register_handler(thinking_handler)

        return self.event_processor

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[object],
    ) -> None:
        """Handle streaming events"""
        logger.debug("Event stream handler started")

        # Ensure processor exists and use the same instance
        if self.event_processor is None:
            self._get_event_processor()

        processor = self.event_processor
        if processor is None:
            raise RuntimeError("Event processor not initialized")

        # Only update game_id if not set - DON'T clear context here
        # This allows events to accumulate across multiple handler calls
        if not processor.context.game_id:
            processor.context.game_id = ctx.deps.game_state.game_id

        # Process the stream - events will be captured in processor.context
        await processor.process_stream(event_stream, ctx)

        logger.debug(f"Captured {len(processor.context.captured_tool_events)} tool events in stream handler")

    # TODO: Refactor process to be simpler to understand and follow. SOLID.
    async def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        # Clear event processor context for new request
        # This ensures we start fresh and don't mix events from previous requests
        if self.event_processor:
            self.event_processor.context.clear()
            self.event_processor.context.game_id = game_state.game_id

        # Update event logger with game ID
        self.event_logger.game_id = game_state.game_id

        # Create dependencies
        deps = AgentDependencies(
            game_state=game_state,
            game_service=game_service,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
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
            # Ensure event processor exists (will be used by event_stream_handler)
            if self.event_processor is None:
                self._get_event_processor()

            # For MVP, we'll use non-streaming but still capture tool events
            logger.debug(f"Starting response generation (stream={stream})")

            # Run the agent with event handler to capture and broadcast tool calls
            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,
            )

            logger.debug(f"Response generated: {result.output[:100]}...")

            all_commands = []

            # Extract commands from tool results (captured by event_stream_handler)
            captured_events = self.event_processor.context.captured_tool_events if self.event_processor else []
            for event in captured_events:
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

            # Get all known NPCs - combine game state NPCs and scenario NPCs
            # Pass NPCSheet objects from game state, and string names from scenario
            all_known_npcs: list[NPCSheet | str] = list(game_state.npcs)
            known_names = {npc.name for npc in game_state.npcs}

            # Add scenario NPCs from current location if available
            if game_state.scenario_id and game_state.current_location_id:
                try:
                    scenario = self.scenario_service.get_scenario(game_state.scenario_id)
                    if scenario:
                        current_location = scenario.get_location(game_state.current_location_id)
                        if current_location and current_location.npcs:
                            # Add scenario NPC names as strings
                            for scenario_npc in current_location.npcs:
                                if scenario_npc.name not in known_names:
                                    all_known_npcs.append(scenario_npc.name)
                                    known_names.add(scenario_npc.name)
                except Exception as e:
                    logger.error(f"Failed to get scenario NPCs: {e}")

            player_npcs = self.metadata_service.extract_npc_mentions(prompt, all_known_npcs)
            dm_npcs = self.metadata_service.extract_npc_mentions(result.output, all_known_npcs)
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

            # Save captured game events (captured by event_stream_handler)
            captured_events = self.event_processor.context.captured_tool_events if self.event_processor else []
            logger.debug(f"Saving {len(captured_events)} captured events to game state")
            for event in captured_events:
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
