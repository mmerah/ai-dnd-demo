"""Agent that handles all narrative D&D gameplay."""

import logging
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.event_stream.base import EventContext, EventStreamProcessor
from app.agents.core.event_stream.thinking import ThinkingHandler
from app.agents.core.event_stream.tools import ToolEventHandler
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IGameService,
    IItemRepository,
    IMetadataService,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState, MessageRole
from app.services.ai.context_service import ContextService
from app.services.ai.event_logger_service import EventLoggerService
from app.services.ai.message_converter_service import MessageConverterService
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
    metadata_service: IMetadataService
    event_bus: IEventBus
    scenario_service: IScenarioService
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
    _event_processor: EventStreamProcessor | None = None

    @property
    def event_processor(self) -> EventStreamProcessor:
        """Get or create the event processor lazily."""
        if self._event_processor is None:
            context = EventContext(game_id="")
            self._event_processor = EventStreamProcessor(context)

            tool_handler = ToolEventHandler(self.event_logger)
            for handler in tool_handler.get_handlers():
                self._event_processor.register_handler(handler)

            thinking_handler = ThinkingHandler(self.event_logger)
            self._event_processor.register_handler(thinking_handler)

        return self._event_processor

    def get_required_tools(self) -> list[ToolFunction]:
        """Return list of tools this agent requires."""
        return [
            dice_tools.roll_dice,
            character_tools.update_hp,
            character_tools.update_condition,
            character_tools.update_spell_slots,
            inventory_tools.modify_currency,
            inventory_tools.modify_inventory,
            time_tools.short_rest,
            time_tools.long_rest,
            time_tools.advance_time,
            location_tools.change_location,
            location_tools.discover_secret,
            location_tools.update_location_state,
            combat_tools.start_combat,
            combat_tools.trigger_scenario_encounter,
            combat_tools.spawn_monsters,
            quest_tools.start_quest,
            quest_tools.complete_objective,
            quest_tools.complete_quest,
            quest_tools.progress_act,
        ]

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[object],
    ) -> None:
        """Handle streaming events"""
        logger.debug("Event stream handler started")
        processor = self.event_processor
        if not processor.context.game_id:
            processor.context.game_id = ctx.deps.game_state.game_id
        await processor.process_stream(event_stream, ctx)
        logger.debug(
            f"Captured {len(processor.context.processed_tool_calls)} tool events in stream handler",
        )

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        if self.event_processor:
            self.event_processor.context.clear()
            self.event_processor.context.game_id = game_state.game_id

        self.event_logger.game_id = game_state.game_id

        deps = AgentDependencies(
            game_state=game_state,
            game_service=game_service,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
        )

        context = self.context_service.build_context(game_state)
        message_history = self.message_converter.to_pydantic_messages(
            game_state.conversation_history,
            agent_type="narrative",
        )

        full_prompt = f"\n\n{context}\n\nPlayer: {prompt}"
        logger.debug(f"Processing prompt: {prompt[:100]}... (stream={stream})")

        try:
            _ = self.event_processor
            logger.debug(f"Starting response generation (stream={stream})")

            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,
            )

            logger.debug(f"Response generated: {result.output[:100]}...")

            # Broadcast final narrative via SSE
            await self.event_bus.submit_and_wait(
                [
                    BroadcastNarrativeCommand(game_id=game_state.game_id, content=result.output, is_complete=False),
                    BroadcastNarrativeCommand(game_id=game_state.game_id, content="", is_complete=True),
                ],
            )

            # Record messages (let GameService extract metadata)
            game_service.add_message(game_state.game_id, MessageRole.PLAYER, prompt, agent_type="narrative")
            game_service.add_message(game_state.game_id, MessageRole.DM, result.output, agent_type="narrative")

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=result.output),
            )

        except Exception as e:
            self.event_logger.log_error(e)
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e),
                metadata={"error_type": type(e).__name__},
            )
            raise
