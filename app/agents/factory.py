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
from app.interfaces.services import (
    IItemRepository,
    IMetadataService,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.services.ai import ContextService, EventLoggerService, MessageConverterService

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
        event_bus: IEventBus | None = None,
        scenario_service: IScenarioService | None = None,
        item_repository: IItemRepository | None = None,
        monster_repository: IMonsterRepository | None = None,
        spell_repository: ISpellRepository | None = None,
        metadata_service: IMetadataService | None = None,
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

            # Create narrative agent instance
            if not event_bus:
                raise ValueError("Event bus is required for narrative agent")
            if not scenario_service:
                raise ValueError("ScenarioService is required for NarrativeAgent")
            if not item_repository or not monster_repository or not spell_repository:
                raise ValueError("Repositories are required for NarrativeAgent")
            if not metadata_service:
                raise ValueError("MetadataService is required for NarrativeAgent")

            narrative_agent = NarrativeAgent(
                agent=agent,
                context_service=ContextService(scenario_service, item_repository, monster_repository, spell_repository),
                message_converter=MessageConverterService(),
                event_logger=EventLoggerService(game_id="", debug=debug),
                metadata_service=metadata_service,
                event_bus=event_bus,
                scenario_service=scenario_service,
                item_repository=item_repository,
                monster_repository=monster_repository,
                spell_repository=spell_repository,
            )

            # Register its required tools
            cls._register_agent_tools(agent, narrative_agent.get_required_tools())

            return narrative_agent

        if agent_type == AgentType.COMBAT:
            raise NotImplementedError("Combat agent not yet implemented")

        if agent_type == AgentType.SUMMARIZER:
            raise NotImplementedError("Summarizer agent not yet implemented")

        raise ValueError(f"Unknown agent type: {agent_type}")
