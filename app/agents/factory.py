"""Factory for creating specialized agents following Factory pattern."""

import logging

import httpx
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.dependencies import AgentDependencies
from app.agents.core.prompts import NARRATIVE_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.agents.narrative.agent import NarrativeAgent
from app.config import get_settings
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IContextService, IEventLoggerService
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

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating specialized agents following Factory pattern."""

    @classmethod
    def _create_model(cls) -> OpenAIModel:
        """Create the AI model with proper configuration."""
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

        return OpenAIModel(settings.openrouter_model, provider=provider)

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
        debug: bool = False,
    ) -> BaseAgent:
        """Create a specialized agent based on type."""
        settings = get_settings()
        model = cls._create_model()
        model_settings = ModelSettings(temperature=0.7, max_tokens=4096, parallel_tool_calls=True)

        if agent_type == AgentType.NARRATIVE:
            agent: Agent[AgentDependencies, str] = Agent(
                model=model,
                deps_type=AgentDependencies,
                system_prompt=NARRATIVE_SYSTEM_PROMPT,
                model_settings=model_settings,
                retries=settings.max_retries,
            )

            narrative_agent = NarrativeAgent(
                agent=agent,
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
            )

            # Register its required tools
            cls._register_agent_tools(agent, narrative_agent.get_required_tools())

            return narrative_agent

        if agent_type == AgentType.COMBAT:
            raise NotImplementedError("Combat agent not yet implemented")

        if agent_type == AgentType.SUMMARIZER:
            raise NotImplementedError("Summarizer agent not yet implemented")

        raise ValueError(f"Unknown agent type: {agent_type}")
