"""Factory for creating specialized agents following Factory pattern."""

import logging

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from app.agents.combat.agent import CombatAgent
from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.prompts import COMBAT_SYSTEM_PROMPT, NARRATIVE_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.agents.narrative.agent import NarrativeAgent
from app.agents.summarizer.agent import SummarizerAgent
from app.config import get_settings
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
from app.services.ai import MessageConverterService
from app.services.ai.debug_logger import AgentDebugLogger

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents following Factory pattern."""

    @classmethod
    def _create_model(cls, model_name: str) -> OpenAIModel:
        """Create the AI model with proper configuration.

        Args:
            model_name: Specific model name
        """
        settings = get_settings()

        headers = {
            "HTTP-Referer": "http://localhost:8123",
            "X-Title": "D&D AI Dungeon Master",
        }

        http_client = httpx.AsyncClient(headers=headers)

        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            http_client=http_client,
        )

        # Use provided model name
        return OpenAIModel(model_name, provider=provider)

    @classmethod
    def _register_agent_tools(cls, agent: Agent[AgentDependencies, str], tools: list[ToolFunction]) -> None:
        """Register tools with an agent."""
        for tool in tools:
            agent.tool(tool)
        logger.info(f"Registered {len(tools)} tools with the agent")

    @classmethod
    def create_agent(
        cls,
        agent_type: AgentType,
        event_bus: IEventBus,
        scenario_service: IScenarioService,
        item_repository: IItemRepository,
        monster_repository: IMonsterRepository,
        spell_repository: ISpellRepository,
        metadata_service: IMetadataService,
        message_manager: IMessageManager,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        conversation_service: IConversationService,
        context_service: IContextService,
        event_logger_service: IEventLoggerService,
        tool_call_extractor_service: IToolCallExtractorService | None = None,
        debug: bool = False,
    ) -> BaseAgent:
        """Create a specialized agent based on type."""
        settings = get_settings()
        # No parallel tool call to avoid the AI getting confused by what it is doing
        model_settings = OpenAIModelSettings(
            temperature=0.7, max_tokens=4096, parallel_tool_calls=False, openai_reasoning_effort="high"
        )

        # Create debug logger if enabled
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        if agent_type == AgentType.NARRATIVE:
            model = cls._create_model(settings.get_narrative_model())
            narrative_pydantic_agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=NARRATIVE_SYSTEM_PROMPT,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            narrative_agent = NarrativeAgent(
                agent=narrative_pydantic_agent,
                context_service=context_service,
                message_converter=MessageConverterService(),
                event_logger=event_logger_service,
                metadata_service=metadata_service,
                event_bus=event_bus,
                scenario_service=scenario_service,
                item_repository=item_repository,
                monster_repository=monster_repository,
                spell_repository=spell_repository,
                message_manager=message_manager,
                save_manager=save_manager,
                event_manager=event_manager,
                conversation_service=conversation_service,
                debug_logger=debug_logger,
            )

            # Register its required tools
            cls._register_agent_tools(narrative_pydantic_agent, narrative_agent.get_required_tools())

            return narrative_agent

        if agent_type == AgentType.COMBAT:
            model = cls._create_model(settings.get_combat_model())
            combat_pydantic_agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=COMBAT_SYSTEM_PROMPT,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            combat_agent = CombatAgent(
                agent=combat_pydantic_agent,
                context_service=context_service,
                message_converter=MessageConverterService(),
                event_logger=event_logger_service,
                metadata_service=metadata_service,
                event_bus=event_bus,
                scenario_service=scenario_service,
                item_repository=item_repository,
                monster_repository=monster_repository,
                spell_repository=spell_repository,
                message_manager=message_manager,
                save_manager=save_manager,
                event_manager=event_manager,
                conversation_service=conversation_service,
                tool_call_extractor=tool_call_extractor_service,
                debug_logger=debug_logger,
            )

            # Register combat-specific tools only
            cls._register_agent_tools(combat_pydantic_agent, combat_agent.get_required_tools())

            return combat_agent

        if agent_type == AgentType.SUMMARIZER:
            model = cls._create_model(settings.get_summarizer_model())
            # Summarizer doesn't need dependencies, so we create a simpler agent
            agent: Agent[None, str] = Agent(
                model=model,
                system_prompt=SUMMARIZER_SYSTEM_PROMPT,
                model_settings=ModelSettings(temperature=0.5, max_tokens=500),
                retries=settings.max_retries,
            )

            summarizer_agent = SummarizerAgent(agent=agent, context_service=context_service)
            # Summarizer doesn't need tools
            return summarizer_agent

        raise ValueError(f"Unknown agent type: {agent_type}")
