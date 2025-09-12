"""Combat agent for tactical combat management."""

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
from app.agents.core.prompts import COMBAT_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.events.commands.broadcast_commands import BroadcastNarrativeCommand
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService, IEventLoggerService, IToolCallExtractorService
from app.interfaces.services.data import IItemRepository, IMonsterRepository, ISpellRepository
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMessageManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.ai_response import NarrativeResponse, StreamEvent, StreamEventType
from app.models.game_state import GameState, MessageRole
from app.services.ai.debug_logger import AgentDebugLogger
from app.services.ai.message_converter_service import MessageConverterService
from app.tools import character_tools, combat_tools, dice_tools

logger = logging.getLogger(__name__)


@dataclass
class CombatAgent(BaseAgent):
    """Agent specialized for tactical combat resolution."""

    agent: Agent[AgentDependencies, str]
    context_service: IContextService
    message_converter: MessageConverterService
    event_logger: IEventLoggerService
    metadata_service: IMetadataService
    event_bus: IEventBus
    scenario_service: IScenarioService
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
    message_manager: IMessageManager
    save_manager: ISaveManager
    event_manager: IEventManager
    conversation_service: IConversationService
    tool_call_extractor: IToolCallExtractorService | None = None
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
        """Return list of combat-specific tools only."""
        return [
            # Dice tools for all rolls
            dice_tools.roll_dice,
            # Character state management
            character_tools.update_hp,
            character_tools.update_condition,
            # Combat flow management - CRITICAL
            combat_tools.next_turn,  # MANDATORY after each turn
            combat_tools.end_combat,
            combat_tools.add_combatant,
            combat_tools.remove_combatant,
        ]

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[object],
    ) -> None:
        """Handle streaming events during combat."""
        logger.debug("Combat event stream handler started")
        processor = self.event_processor
        if not processor.context.game_id:
            processor.context.game_id = ctx.deps.game_state.game_id
        await processor.process_stream(event_stream, ctx)
        logger.debug(
            f"Captured {len(processor.context.processed_tool_calls)} tool events in combat stream",
        )

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process a combat action and yield stream events."""
        self.event_processor.context.clear()
        self.event_processor.context.game_id = game_state.game_id

        self.event_logger.set_game_id(game_state.game_id)
        self.event_logger.set_agent_type(AgentType.COMBAT.value)

        deps = AgentDependencies(
            game_state=game_state,
            event_bus=self.event_bus,
            agent_type=AgentType.COMBAT,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
            message_manager=self.message_manager,
            event_manager=self.event_manager,
            metadata_service=self.metadata_service,
            save_manager=self.save_manager,
        )

        # Build combat-focused context
        context = self.context_service.build_context(game_state, AgentType.COMBAT)
        message_history = self.message_converter.to_pydantic_messages(
            game_state.conversation_history,
            agent_type=AgentType.COMBAT,
        )

        full_prompt = f"\n\n{context}\n\nPlayer Action: {prompt}"
        logger.info(f"Combat agent processing: {prompt[:100]}... (stream={stream})")

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
                agent_type=AgentType.COMBAT,
                game_id=game_state.game_id,
                system_prompt=COMBAT_SYSTEM_PROMPT,
                conversation_history=conv_history,
                user_prompt=prompt,
                context=context,
            )

        try:
            result = await self.agent.run(
                full_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,
            )

            logger.debug(f"Combat response generated: {result.output[:100]}...")

            # Check for any tool calls in the narrative output and execute them
            if self.tool_call_extractor:
                extracted_tools = self.tool_call_extractor.extract_tool_calls(result.output)
                if extracted_tools:
                    logger.warning(f"Found {len(extracted_tools)} tool calls in narrative output - executing them")
                    for tool_call in extracted_tools:
                        success = await self.tool_call_extractor.execute_extracted_tool_call(
                            tool_call, game_state, AgentType.COMBAT
                        )
                        if success:
                            logger.info(f"Successfully executed extracted tool: {tool_call.get('function')}")
                        else:
                            logger.error(f"Failed to execute extracted tool: {tool_call.get('function')}")

            # Broadcast combat narrative via SSE
            await self.event_bus.submit_and_wait(
                [
                    BroadcastNarrativeCommand(game_id=game_state.game_id, content=result.output, is_complete=False),
                    BroadcastNarrativeCommand(game_id=game_state.game_id, content="", is_complete=True),
                ],
            )

            # Record combat messages
            self.conversation_service.record_message(game_state, MessageRole.PLAYER, prompt, AgentType.COMBAT)
            self.conversation_service.record_message(game_state, MessageRole.DM, result.output, AgentType.COMBAT)

            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=NarrativeResponse(narrative=result.output),
            )

        except Exception as e:
            logger.error(f"Combat agent error: {e}", exc_info=True)
            self.event_logger.log_error(e)
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(e),
                metadata={"error_type": type(e).__name__},
            )
