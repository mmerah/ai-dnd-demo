"""Shared infrastructure for NPC agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    TextPart,
    UserPromptPart,
)

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.event_stream.base import EventContext, EventStreamProcessor
from app.agents.core.event_stream.thinking import ThinkingHandler
from app.agents.core.event_stream.tools import ToolEventHandler
from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService, IEventLoggerService, IMessageService
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
from app.models.instances.npc_instance import NPCInstance
from app.services.ai.debug_logger import AgentDebugLogger
from app.services.ai.message_converter_service import MessageConverterService
from app.tools import inventory_tools, location_tools, quest_tools

logger = logging.getLogger(__name__)


class BaseNPCAgent(BaseAgent, ABC):
    """Common logic for NPC agents (individual minds & puppeteers)."""

    def __init__(
        self,
        *,
        agent: Agent[AgentDependencies, str],
        context_service: IContextService,
        message_converter: MessageConverterService,
        event_logger: IEventLoggerService,
        metadata_service: IMetadataService,
        event_bus: IEventBus,
        conversation_service: IConversationService,
        scenario_service: IScenarioService,
        repository_provider: IRepositoryProvider,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        action_service: IActionService,
        message_service: IMessageService,
        debug_logger: AgentDebugLogger | None = None,
        system_prompt: str = "",
    ) -> None:
        self.agent = agent
        self.context_service = context_service
        self.message_converter = message_converter
        self.event_logger = event_logger
        self.metadata_service = metadata_service
        self.event_bus = event_bus
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.debug_logger = debug_logger
        self._scenario_service = scenario_service
        self._repository_provider = repository_provider
        self._event_manager = event_manager
        self._save_manager = save_manager
        self._action_service = action_service
        self._event_processor: EventStreamProcessor | None = None
        self._active_npc: NPCInstance | None = None
        self._system_prompt = system_prompt

    @property
    def event_processor(self) -> EventStreamProcessor:
        if self._event_processor is None:
            context = EventContext(game_id="")
            self._event_processor = EventStreamProcessor(context)

            tool_handler = ToolEventHandler(self.event_logger)
            for handler in tool_handler.get_handlers():
                self._event_processor.register_handler(handler)

            thinking_handler = ThinkingHandler(self.event_logger)
            self._event_processor.register_handler(thinking_handler)

        return self._event_processor

    async def event_stream_handler(
        self,
        ctx: RunContext[AgentDependencies],
        event_stream: AsyncIterable[object],
    ) -> None:
        logger.debug("NPC agent event stream handler started")
        processor = self.event_processor
        if not processor.context.game_id:
            processor.context.game_id = ctx.deps.game_state.game_id
        await processor.process_stream(event_stream, ctx)
        logger.debug(
            "Captured %s tool events in NPC stream handler",
            len(processor.context.processed_tool_calls),
        )

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        context: str,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process the player's prompt and generate an NPC reply.

        Note: The context parameter is unused for NPC agents. NPCs build their own
        context internally since it includes NPC-specific persona information.
        """
        npc = self._require_active_npc()
        self.event_processor.context.clear()
        self.event_processor.context.game_id = game_state.game_id

        self.event_logger.set_game_id(game_state.game_id)
        self.event_logger.set_agent_type(AgentType.NPC.value)

        deps = self._build_agent_dependencies(game_state)
        context_text = self._build_context(game_state, npc)
        message_history = self._build_message_history(game_state)
        npc_prompt = self._build_prompt(prompt, npc, game_state, context_text)

        if self.debug_logger:
            self.debug_logger.log_agent_call(
                agent_type=AgentType.NPC,
                game_id=game_state.game_id,
                system_prompt=self._get_system_prompt(),
                conversation_history=[self._model_message_to_dict(msg) for msg in message_history],
                user_prompt=prompt,
                context=context_text,
                npc_instance_id=npc.instance_id,
            )

        try:
            result = await self.agent.run(
                npc_prompt,
                deps=deps,
                message_history=message_history,
                event_stream_handler=self.event_stream_handler,
            )
        except Exception as exc:  # pragma: no cover - fail fast path mirrors other agents
            self.event_logger.log_error(exc)
            yield StreamEvent(
                type=StreamEventType.ERROR,
                content=str(exc),
                metadata={"error_type": type(exc).__name__},
            )
            raise
        finally:
            self._active_npc = None

        reply_text = result.output
        logger.debug("NPC agent %s produced reply length=%s", npc.instance_id, len(reply_text))

        await self._broadcast_npc_dialogue(game_state, npc, reply_text)
        self.conversation_service.record_message(
            game_state,
            MessageRole.NPC,
            reply_text,
            agent_type=AgentType.NPC,
            speaker_npc_id=npc.instance_id,
            speaker_npc_name=npc.display_name,
        )

        yield StreamEvent(
            type=StreamEventType.COMPLETE,
            content=NarrativeResponse(narrative=reply_text),
            metadata={"npc_id": npc.instance_id, "npc_name": npc.display_name},
        )

    def _build_agent_dependencies(self, game_state: GameState) -> AgentDependencies:
        return AgentDependencies(
            game_state=game_state,
            event_bus=self.event_bus,
            agent_type=AgentType.NPC,
            scenario_service=self._scenario_service,
            item_repository=self._repository_provider.get_item_repository_for(game_state),
            monster_repository=self._repository_provider.get_monster_repository_for(game_state),
            spell_repository=self._repository_provider.get_spell_repository_for(game_state),
            conversation_service=self.conversation_service,
            event_manager=self._event_manager,
            metadata_service=self.metadata_service,
            save_manager=self._save_manager,
            action_service=self._action_service,
        )

    @abstractmethod
    def _build_context(self, game_state: GameState, npc: NPCInstance) -> str:
        """Build the context string for the agent invocation."""

    @abstractmethod
    def _build_prompt(
        self,
        player_message: str,
        npc: NPCInstance,
        game_state: GameState,
        context_text: str,
    ) -> str:
        """Build the user prompt to send to the underlying model."""

    async def _broadcast_npc_dialogue(self, game_state: GameState, npc: NPCInstance, content: str) -> None:
        """Send the NPC reply to connected clients via the message service."""

        await self.message_service.send_npc_dialogue(
            game_id=game_state.game_id,
            npc_id=npc.instance_id,
            npc_name=npc.display_name,
            content=content,
            complete=True,
        )

    def get_required_tools(self) -> list[ToolFunction]:
        """Return list of tools this agent requires."""
        return [
            quest_tools.start_quest,
            quest_tools.complete_objective,
            quest_tools.complete_quest,
            inventory_tools.modify_inventory,
            location_tools.update_location_state,
            location_tools.discover_secret,
            location_tools.move_npc_to_location,
        ]

    def _build_message_history(self, game_state: GameState) -> list[ModelMessage]:
        active_npc = self._require_active_npc()
        return self.message_converter.to_pydantic_messages(
            messages=game_state.conversation_history,
            agent_type=AgentType.NPC,
            game_state=game_state,
            npc_id=active_npc.instance_id,
        )

    def prepare_for_npc(self, npc: NPCInstance) -> None:
        """Assign the NPC this agent should embody for the next response."""
        self._active_npc = npc

    def _require_active_npc(self) -> NPCInstance:
        if self._active_npc is None:  # pragma: no cover
            raise RuntimeError("NPC agent invoked without an active NPC context")
        return self._active_npc

    @staticmethod
    def _model_message_to_dict(message: ModelMessage) -> dict[str, str]:
        """Convert pydantic_ai ModelMessage to dict for logging."""
        if isinstance(message, ModelRequest):
            chunks = [str(part.content) for part in message.parts if isinstance(part, UserPromptPart)]
            return {"role": "user", "content": "".join(chunks)}
        else:
            chunks = [str(part.content) for part in message.parts if isinstance(part, TextPart)]
            return {"role": "assistant", "content": "".join(chunks)}

    def _get_system_prompt(self) -> str:
        """Return the configured system prompt for debug logging."""
        return self._system_prompt
