"""Factory for creating specialized agents."""

import logging
from typing import cast

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from app.agents.combat.agent import CombatAgent
from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.prompts import (
    COMBAT_SYSTEM_PROMPT,
    NARRATIVE_SYSTEM_PROMPT,
    NPC_SYSTEM_PROMPT,
    PUPPETEER_SYSTEM_PROMPT,
    SUMMARIZER_SYSTEM_PROMPT,
)
from app.agents.core.types import AgentType
from app.agents.narrative.agent import NarrativeAgent
from app.agents.npc import IndividualMindAgent, PuppeteerAgent
from app.agents.summarizer.agent import SummarizerAgent
from app.config import get_settings
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import (
    IContextService,
    IEventLoggerService,
    IMessageService,
    IToolCallExtractorService,
)
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.services.ai import MessageConverterService
from app.services.ai.debug_logger import AgentDebugLogger

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents."""

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
        repository_provider: IRepositoryProvider,
        metadata_service: IMetadataService,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        conversation_service: IConversationService,
        context_service: IContextService,
        event_logger_service: IEventLoggerService,
        tool_call_extractor_service: IToolCallExtractorService,
        action_service: IActionService,
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
                repository_provider=repository_provider,
                save_manager=save_manager,
                event_manager=event_manager,
                conversation_service=conversation_service,
                action_service=action_service,
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
                repository_provider=repository_provider,
                save_manager=save_manager,
                event_manager=event_manager,
                conversation_service=conversation_service,
                tool_call_extractor=tool_call_extractor_service,
                action_service=action_service,
                debug_logger=debug_logger,
            )

            # Register combat-specific tools only
            cls._register_agent_tools(combat_pydantic_agent, combat_agent.get_required_tools())

            return combat_agent

        if agent_type == AgentType.SUMMARIZER:
            model = cls._create_model(settings.get_summarizer_model())
            summarizer_settings = OpenAIModelSettings(temperature=0.5, max_tokens=1000, parallel_tool_calls=False)
            # Summarizer doesn't need dependencies, so we create a simpler agent
            agent: Agent[None, str] = Agent(
                model=model,
                system_prompt=SUMMARIZER_SYSTEM_PROMPT,
                model_settings=summarizer_settings,
                retries=settings.max_retries,
            )

            summarizer_agent: ISummarizerAgent = SummarizerAgent(
                agent=agent,
                context_service=context_service,
                debug_logger=debug_logger,
            )
            # Summarizer doesn't need tools
            return cast(BaseAgent, summarizer_agent)

        raise ValueError(f"Unknown agent type: {agent_type}")

    @classmethod
    def create_individual_mind_agent(
        cls,
        *,
        event_bus: IEventBus,
        scenario_service: IScenarioService,
        repository_provider: IRepositoryProvider,
        metadata_service: IMetadataService,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        conversation_service: IConversationService,
        context_service: IContextService,
        event_logger_service: IEventLoggerService,
        action_service: IActionService,
        message_service: IMessageService,
        debug: bool = False,
    ) -> IndividualMindAgent:
        settings = get_settings()
        model = cls._create_model(settings.get_narrative_model())
        model_settings = OpenAIModelSettings(
            temperature=0.7,
            max_tokens=2048,
            parallel_tool_calls=False,
            openai_reasoning_effort="medium",
        )
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        npc_agent_core: Agent[AgentDependencies, str] = Agent(
            model=model,
            deps_type=AgentDependencies,
            system_prompt=NPC_SYSTEM_PROMPT,
            model_settings=model_settings,
            retries=settings.max_retries,
        )

        individual_agent = IndividualMindAgent(
            agent=npc_agent_core,
            context_service=context_service,
            message_converter=MessageConverterService(),
            event_logger=event_logger_service,
            metadata_service=metadata_service,
            event_bus=event_bus,
            conversation_service=conversation_service,
            scenario_service=scenario_service,
            repository_provider=repository_provider,
            event_manager=event_manager,
            save_manager=save_manager,
            action_service=action_service,
            message_service=message_service,
            debug_logger=debug_logger,
        )

        cls._register_agent_tools(npc_agent_core, individual_agent.get_required_tools())
        return individual_agent

    @classmethod
    def create_puppeteer_agent(
        cls,
        *,
        event_bus: IEventBus,
        scenario_service: IScenarioService,
        repository_provider: IRepositoryProvider,
        metadata_service: IMetadataService,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        conversation_service: IConversationService,
        context_service: IContextService,
        event_logger_service: IEventLoggerService,
        action_service: IActionService,
        message_service: IMessageService,
        debug: bool = False,
    ) -> PuppeteerAgent:
        settings = get_settings()
        model = cls._create_model(settings.get_narrative_model())
        model_settings = OpenAIModelSettings(
            temperature=0.8,
            max_tokens=2048,
            parallel_tool_calls=False,
            openai_reasoning_effort="medium",
        )
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        puppeteer_core: Agent[AgentDependencies, str] = Agent(
            model=model,
            deps_type=AgentDependencies,
            system_prompt=PUPPETEER_SYSTEM_PROMPT,
            model_settings=model_settings,
            retries=settings.max_retries,
        )

        puppeteer_agent = PuppeteerAgent(
            agent=puppeteer_core,
            context_service=context_service,
            message_converter=MessageConverterService(),
            event_logger=event_logger_service,
            metadata_service=metadata_service,
            event_bus=event_bus,
            conversation_service=conversation_service,
            scenario_service=scenario_service,
            repository_provider=repository_provider,
            event_manager=event_manager,
            save_manager=save_manager,
            action_service=action_service,
            message_service=message_service,
            debug_logger=debug_logger,
        )

        cls._register_agent_tools(puppeteer_core, puppeteer_agent.get_required_tools())
        return puppeteer_agent
