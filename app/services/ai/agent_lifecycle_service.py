"""Lifecycle management for NPC agents."""

from __future__ import annotations

import logging
from collections import defaultdict

from app.agents.factory import AgentFactory
from app.agents.npc import IndividualMindAgent, PuppeteerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService, IEventLoggerService, IMessageService
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMessageManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance
from app.models.npc import NPCImportance

logger = logging.getLogger(__name__)


class AgentLifecycleService(IAgentLifecycleService):
    """Create and cache NPC agents per game, respecting NPC importance."""

    def __init__(
        self,
        *,
        event_bus: IEventBus,
        scenario_service: IScenarioService,
        repository_provider: IRepositoryProvider,
        metadata_service: IMetadataService,
        message_manager: IMessageManager,
        event_manager: IEventManager,
        save_manager: ISaveManager,
        conversation_service: IConversationService,
        context_service: IContextService,
        event_logger_service: IEventLoggerService,
        action_service: IActionService,
        message_service: IMessageService,
        debug: bool = False,
    ) -> None:
        self._event_bus = event_bus
        self._scenario_service = scenario_service
        self._repository_provider = repository_provider
        self._metadata_service = metadata_service
        self._message_manager = message_manager
        self._event_manager = event_manager
        self._save_manager = save_manager
        self._conversation_service = conversation_service
        self._context_service = context_service
        self._event_logger_service = event_logger_service
        self._action_service = action_service
        self._message_service = message_service
        self._debug = debug

        self._individual_agents: dict[str, dict[str, IndividualMindAgent]] = defaultdict(dict)
        self._puppeteer_agents: dict[str, PuppeteerAgent] = {}

    def get_npc_agent(self, game_state: GameState, npc: NPCInstance) -> IndividualMindAgent | PuppeteerAgent:
        """Return a cached or newly-created agent for the given NPC."""
        if npc.sheet.importance is NPCImportance.MAJOR:
            return self._get_individual_agent(game_state, npc)
        return self._get_puppeteer_agent(game_state)

    def release_npc_agent(self, game_id: str, npc_id: str) -> None:
        """Release a cached agent for an NPC (primarily for major NPC churn)."""
        if game_id in self._individual_agents and npc_id in self._individual_agents[game_id]:
            logger.debug("Releasing individual NPC agent cache for npc_id=%s game=%s", npc_id, game_id)
            self._individual_agents[game_id].pop(npc_id, None)
            if not self._individual_agents[game_id]:
                self._individual_agents.pop(game_id, None)

    def release_for_game(self, game_id: str) -> None:
        """Clear all cached agents associated with a game (e.g., when game ends)."""
        self._individual_agents.pop(game_id, None)
        self._puppeteer_agents.pop(game_id, None)

    def _get_individual_agent(self, game_state: GameState, npc: NPCInstance) -> IndividualMindAgent:
        game_agents = self._individual_agents[game_state.game_id]
        if npc.instance_id not in game_agents:
            logger.debug("Creating IndividualMindAgent for npc_id=%s", npc.instance_id)
            agent = AgentFactory.create_individual_mind_agent(
                event_bus=self._event_bus,
                scenario_service=self._scenario_service,
                repository_provider=self._repository_provider,
                metadata_service=self._metadata_service,
                message_manager=self._message_manager,
                event_manager=self._event_manager,
                save_manager=self._save_manager,
                conversation_service=self._conversation_service,
                context_service=self._context_service,
                event_logger_service=self._event_logger_service,
                action_service=self._action_service,
                message_service=self._message_service,
                debug=self._debug,
            )
            game_agents[npc.instance_id] = agent
        return game_agents[npc.instance_id]

    def _get_puppeteer_agent(self, game_state: GameState) -> PuppeteerAgent:
        if game_state.game_id not in self._puppeteer_agents:
            logger.debug("Creating shared PuppeteerAgent for game=%s", game_state.game_id)
            agent = AgentFactory.create_puppeteer_agent(
                event_bus=self._event_bus,
                scenario_service=self._scenario_service,
                repository_provider=self._repository_provider,
                metadata_service=self._metadata_service,
                message_manager=self._message_manager,
                event_manager=self._event_manager,
                save_manager=self._save_manager,
                conversation_service=self._conversation_service,
                context_service=self._context_service,
                event_logger_service=self._event_logger_service,
                action_service=self._action_service,
                message_service=self._message_service,
                debug=self._debug,
            )
            self._puppeteer_agents[game_state.game_id] = agent
        return self._puppeteer_agents[game_state.game_id]
