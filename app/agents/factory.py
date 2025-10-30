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
from app.agents.core.types import AgentType
from app.agents.narrative.agent import NarrativeAgent
from app.agents.npc import IndividualMindAgent, PuppeteerAgent
from app.agents.summarizer.agent import SummarizerAgent
from app.agents.tool_suggestor.agent import ToolSuggestorAgent
from app.config import get_settings
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import (
    IContextService,
    IEventLoggerService,
    IMessageService,
    IToolCallExtractorService,
    IToolSuggestionService,
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
from app.models.agent_config import AgentConfig
from app.services.ai import MessageConverterService
from app.services.ai.config_loader import AgentConfigLoader
from app.services.ai.debug_logger import AgentDebugLogger

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents."""

    def __init__(self, config_loader: AgentConfigLoader) -> None:
        """Initialize factory with configuration loader.

        Args:
            config_loader: Loader for agent configurations

        Raises:
            FileNotFoundError: If config files are missing
            ValueError: If config files are invalid
        """
        self.config_loader = config_loader
        self.narrative_config, self.narrative_prompt = config_loader.load_agent_config("narrative.json")
        self.combat_config, self.combat_prompt = config_loader.load_agent_config("combat.json")
        self.summarizer_config, self.summarizer_prompt = config_loader.load_agent_config("summarizer.json")
        self.npc_individual_config, self.npc_individual_prompt = config_loader.load_agent_config("npc_individual.json")
        self.npc_puppeteer_config, self.npc_puppeteer_prompt = config_loader.load_agent_config("npc_puppeteer.json")

    def _create_model(self, model_name: str) -> OpenAIModel:
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

    def _register_agent_tools(self, agent: Agent[AgentDependencies, str], tools: list[ToolFunction]) -> None:
        """Register tools with an agent."""
        for tool in tools:
            agent.tool(tool)
        logger.info(f"Registered {len(tools)} tools with the agent")

    def _config_to_model_settings(self, config: AgentConfig) -> OpenAIModelSettings:
        """Convert agent config to PydanticAI model settings.

        Args:
            config: Agent configuration

        Returns:
            OpenAIModelSettings instance
        """
        return OpenAIModelSettings(
            temperature=config.agent_model_config.temperature,
            max_tokens=config.agent_model_config.max_tokens,
            parallel_tool_calls=config.agent_model_config.parallel_tool_calls,
            openai_reasoning_effort=config.agent_model_config.reasoning_effort,
        )

    def create_agent(
        self,
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

        # Create debug logger if enabled
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        if agent_type == AgentType.NARRATIVE:
            model = self._create_model(settings.get_narrative_model())
            model_settings = self._config_to_model_settings(self.narrative_config)

            narrative_pydantic_agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=self.narrative_prompt,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            narrative_agent = NarrativeAgent(
                agent=narrative_pydantic_agent,
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
                system_prompt=self.narrative_prompt,
                debug_logger=debug_logger,
            )

            # Register its required tools
            self._register_agent_tools(narrative_pydantic_agent, narrative_agent.get_required_tools())

            return narrative_agent

        if agent_type == AgentType.COMBAT:
            model = self._create_model(settings.get_combat_model())
            model_settings = self._config_to_model_settings(self.combat_config)

            combat_pydantic_agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=self.combat_prompt,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            combat_agent = CombatAgent(
                agent=combat_pydantic_agent,
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
                system_prompt=self.combat_prompt,
                debug_logger=debug_logger,
            )

            # Register combat-specific tools only
            self._register_agent_tools(combat_pydantic_agent, combat_agent.get_required_tools())

            return combat_agent

        if agent_type == AgentType.SUMMARIZER:
            model = self._create_model(settings.get_summarizer_model())
            model_settings = self._config_to_model_settings(self.summarizer_config)

            # Summarizer doesn't need dependencies, so we create a simpler agent
            agent: Agent[None, str] = Agent(
                model=model,
                system_prompt=self.summarizer_prompt,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            summarizer_agent: ISummarizerAgent = SummarizerAgent(
                agent=agent,
                context_service=context_service,
                system_prompt=self.summarizer_prompt,
                debug_logger=debug_logger,
            )
            # Summarizer doesn't need tools
            return cast(BaseAgent, summarizer_agent)

        raise ValueError(f"Unknown agent type: {agent_type}")

    def create_individual_mind_agent(
        self,
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
        model = self._create_model(settings.get_individual_npc_model())
        model_settings = self._config_to_model_settings(self.npc_individual_config)
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        npc_agent_core: Agent[AgentDependencies, str] = Agent(
            model=model,
            deps_type=AgentDependencies,
            system_prompt=self.npc_individual_prompt,
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
            system_prompt=self.npc_individual_prompt,
            debug_logger=debug_logger,
        )

        self._register_agent_tools(npc_agent_core, individual_agent.get_required_tools())
        return individual_agent

    def create_puppeteer_agent(
        self,
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
        model = self._create_model(settings.get_puppeteer_npc_model())
        model_settings = self._config_to_model_settings(self.npc_puppeteer_config)
        debug_logger = AgentDebugLogger(enabled=settings.debug_agent_context)

        puppeteer_core: Agent[AgentDependencies, str] = Agent(
            model=model,
            deps_type=AgentDependencies,
            system_prompt=self.npc_puppeteer_prompt,
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
            system_prompt=self.npc_puppeteer_prompt,
            debug_logger=debug_logger,
        )

        self._register_agent_tools(puppeteer_core, puppeteer_agent.get_required_tools())
        return puppeteer_agent

    def create_tool_suggestor_agent(self, suggestion_service: IToolSuggestionService) -> ToolSuggestorAgent:
        return ToolSuggestorAgent(suggestion_service=suggestion_service)
