"""Agent that handles all narrative D&D gameplay."""

import logging
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.event_stream.base import EventContext, EventStreamProcessor
from app.agents.core.event_stream.thinking import ThinkingHandler
from app.agents.core.event_stream.tools import ToolEventHandler
from app.agents.core.prompts import NARRATIVE_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService, IEventLoggerService
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState, MessageRole
from app.services.ai.debug_logger import AgentDebugLogger
from app.services.ai.message_converter_service import MessageConverterService
from app.tools import (
    combat_tools,
    dice_tools,
    entity_tools,
    inventory_tools,
    location_tools,
    party_tools,
    quest_tools,
    time_tools,
)

logger = logging.getLogger(__name__)


@dataclass
class NarrativeAgent(BaseAgent):
    """Agent that handles all narrative D&D gameplay."""

    agent: Agent[AgentDependencies, str]
    context_service: IContextService
    message_converter: MessageConverterService
    event_logger: IEventLoggerService
    metadata_service: IMetadataService
    event_bus: IEventBus
    scenario_service: IScenarioService
    repository_provider: IRepositoryProvider
    save_manager: ISaveManager
    event_manager: IEventManager
    conversation_service: IConversationService
    action_service: IActionService
    debug_logger: AgentDebugLogger | None = None
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
            entity_tools.update_hp,
            entity_tools.update_condition,
            entity_tools.update_spell_slots,
            entity_tools.level_up,
            inventory_tools.modify_currency,
            inventory_tools.modify_inventory,
            time_tools.short_rest,
            time_tools.long_rest,
            time_tools.advance_time,
            location_tools.change_location,
            location_tools.discover_secret,
            location_tools.update_location_state,
            location_tools.move_npc_to_location,
            party_tools.add_party_member,
            party_tools.remove_party_member,
            combat_tools.start_combat,
            combat_tools.start_encounter_combat,
            combat_tools.spawn_monsters,
            quest_tools.start_quest,
            quest_tools.complete_objective,
            quest_tools.complete_quest,
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
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a prompt and yield stream events."""
        self.event_processor.context.clear()
        self.event_processor.context.game_id = game_state.game_id

        self.event_logger.set_game_id(game_state.game_id)
        self.event_logger.set_agent_type(AgentType.NARRATIVE.value)

        item_repo = self.repository_provider.get_item_repository_for(game_state)
        monster_repo = self.repository_provider.get_monster_repository_for(game_state)
        spell_repo = self.repository_provider.get_spell_repository_for(game_state)

        deps = AgentDependencies(
            game_state=game_state,
            event_bus=self.event_bus,
            agent_type=AgentType.NARRATIVE,
            scenario_service=self.scenario_service,
            item_repository=item_repo,
            monster_repository=monster_repo,
            spell_repository=spell_repo,
            conversation_service=self.conversation_service,
            event_manager=self.event_manager,
            metadata_service=self.metadata_service,
            save_manager=self.save_manager,
            action_service=self.action_service,
        )

        context = self.context_service.build_context(game_state, AgentType.NARRATIVE)
        message_history = self.message_converter.to_pydantic_messages(
            game_state.conversation_history,
            agent_type=AgentType.NARRATIVE,
        )

        full_prompt = f"\n\n{context}\n\nPlayer: {prompt}"
        logger.debug(f"Processing prompt: {prompt[:100]}... (stream={stream})")

        # Log agent call for debugging if enabled
        if self.debug_logger:
            # Convert pydantic messages to simple dict format for logging
            conv_history = []
            for msg in message_history:
                if isinstance(msg, ModelRequest):
                    # Extract content from UserPromptPart
                    msg_content = ""
                    if msg.parts:
                        for req_part in msg.parts:
                            if isinstance(req_part, UserPromptPart):
                                msg_content = str(req_part.content)
                                break
                    conv_history.append({"role": "user", "content": msg_content})
                elif isinstance(msg, ModelResponse):
                    # Extract content from TextPart
                    msg_content = ""
                    if msg.parts:
                        for resp_part in msg.parts:
                            if isinstance(resp_part, TextPart):
                                msg_content = str(resp_part.content)
                                break
                    conv_history.append({"role": "assistant", "content": msg_content})

            self.debug_logger.log_agent_call(
                agent_type=AgentType.NARRATIVE,
                game_id=game_state.game_id,
                system_prompt=NARRATIVE_SYSTEM_PROMPT,
                conversation_history=conv_history,
                user_prompt=prompt,
                context=context,
            )

        try:
            _ = self.event_processor
            logger.debug(f"Starting response generation (stream={stream})")

            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,
            )

            logger.debug(f"Response generated: {result.output}...")

            # Check if combat was started during this turn
            if self.event_processor.context.combat_started:
                # Minimal response when transitioning to combat
                # The combat agent will handle the actual combat narrative
                logger.info("Combat started during narrative turn - using minimal response")
                short_msg = "Combat has begun!"

                # Broadcast minimal narrative
                await self.event_bus.submit_and_wait(
                    [
                        BroadcastNarrativeCommand(game_id=game_state.game_id, content=short_msg, is_complete=False),
                        BroadcastNarrativeCommand(game_id=game_state.game_id, content="", is_complete=True),
                    ],
                )

                # Record minimal messages
                self.conversation_service.record_message(game_state, MessageRole.PLAYER, prompt, AgentType.NARRATIVE)
                self.conversation_service.record_message(game_state, MessageRole.DM, short_msg, AgentType.NARRATIVE)

                yield StreamEvent(
                    type=StreamEventType.COMPLETE,
                    content=NarrativeResponse(narrative=short_msg),
                )
            else:
                # Normal narrative response
                # Broadcast final narrative via SSE
                await self.event_bus.submit_and_wait(
                    [
                        BroadcastNarrativeCommand(game_id=game_state.game_id, content=result.output, is_complete=False),
                        BroadcastNarrativeCommand(game_id=game_state.game_id, content="", is_complete=True),
                    ],
                )

                # Record messages
                self.conversation_service.record_message(game_state, MessageRole.PLAYER, prompt, AgentType.NARRATIVE)
                self.conversation_service.record_message(game_state, MessageRole.DM, result.output, AgentType.NARRATIVE)

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
