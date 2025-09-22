"""Unit tests for AgentLifecycleService."""

from __future__ import annotations

from typing import cast
from unittest.mock import create_autospec

import pytest

from app.agents.factory import AgentFactory
from app.agents.npc.individual_agent import IndividualMindAgent
from app.agents.npc.puppeteer_agent import PuppeteerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService, IEventLoggerService, IMessageService
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import (
    IConversationService,
    IEventManager,
    IMetadataService,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.npc import NPCImportance
from app.services.ai.agent_lifecycle_service import AgentLifecycleService
from tests.factories import make_game_state, make_npc_instance, make_npc_sheet


@pytest.fixture()
def lifecycle_service(monkeypatch: pytest.MonkeyPatch) -> tuple[IAgentLifecycleService, dict[str, int], dict[str, int]]:
    event_bus = create_autospec(IEventBus, instance=True)
    scenario_service = create_autospec(IScenarioService, instance=True)
    repository_provider = create_autospec(IRepositoryProvider, instance=True)
    metadata_service = create_autospec(IMetadataService, instance=True)
    conversation_service = create_autospec(IConversationService, instance=True)
    event_manager = create_autospec(IEventManager, instance=True)
    save_manager = create_autospec(ISaveManager, instance=True)
    conversation_service = create_autospec(IConversationService, instance=True)
    context_service = create_autospec(IContextService, instance=True)
    event_logger = create_autospec(IEventLoggerService, instance=True)
    action_service = create_autospec(IActionService, instance=True)
    message_service = create_autospec(IMessageService, instance=True)

    creation_counts: dict[str, int] = {"individual": 0}
    puppeteer_counts: dict[str, int] = {"puppeteer": 0}

    def _create_individual(**_: object) -> IndividualMindAgent:
        creation_counts["individual"] += 1
        return cast(IndividualMindAgent, create_autospec(IndividualMindAgent, instance=True))

    def _create_puppeteer(**_: object) -> PuppeteerAgent:
        puppeteer_counts["puppeteer"] += 1
        return cast(PuppeteerAgent, create_autospec(PuppeteerAgent, instance=True))

    monkeypatch.setattr(AgentFactory, "create_individual_mind_agent", _create_individual)
    monkeypatch.setattr(AgentFactory, "create_puppeteer_agent", _create_puppeteer)

    service = AgentLifecycleService(
        event_bus=event_bus,
        scenario_service=scenario_service,
        repository_provider=repository_provider,
        metadata_service=metadata_service,
        event_manager=event_manager,
        save_manager=save_manager,
        conversation_service=conversation_service,
        context_service=context_service,
        event_logger_service=event_logger,
        action_service=action_service,
        message_service=message_service,
    )
    return service, creation_counts, puppeteer_counts


@pytest.mark.asyncio
async def test_major_npc_agents_are_cached(
    lifecycle_service: tuple[IAgentLifecycleService, dict[str, int], dict[str, int]],
) -> None:
    service, creation_counts, _ = lifecycle_service
    game_state = make_game_state()
    npc = make_npc_instance(instance_id="npc-major", npc_sheet=make_npc_sheet(importance=NPCImportance.MAJOR))
    game_state.npcs.append(npc)

    agent_a = service.get_npc_agent(game_state, npc)
    agent_b = service.get_npc_agent(game_state, npc)

    assert agent_a is agent_b
    assert creation_counts["individual"] == 1


@pytest.mark.asyncio
async def test_minor_npc_uses_shared_puppeteer(
    lifecycle_service: tuple[IAgentLifecycleService, dict[str, int], dict[str, int]],
) -> None:
    service, _, puppeteer_counts = lifecycle_service
    game_state = make_game_state()
    npc = make_npc_instance(instance_id="npc-minor")
    npc.sheet.importance = NPCImportance.MINOR
    game_state.npcs.append(npc)

    agent_a = service.get_npc_agent(game_state, npc)
    another_minor = make_npc_instance(instance_id="npc-minor-2")
    another_minor.sheet.importance = NPCImportance.MINOR
    game_state.npcs.append(another_minor)
    agent_b = service.get_npc_agent(game_state, another_minor)

    assert agent_a is agent_b
    assert puppeteer_counts["puppeteer"] == 1


@pytest.mark.asyncio
async def test_release_for_game_clears_caches(
    lifecycle_service: tuple[IAgentLifecycleService, dict[str, int], dict[str, int]],
) -> None:
    service, creation_counts, puppeteer_counts = lifecycle_service
    game_state = make_game_state()
    npc_major = make_npc_instance(instance_id="npc-major")
    npc_major.sheet.importance = NPCImportance.MAJOR
    npc_minor = make_npc_instance(instance_id="npc-minor")
    npc_minor.sheet.importance = NPCImportance.MINOR

    service.get_npc_agent(game_state, npc_major)
    service.get_npc_agent(game_state, npc_minor)
    service.release_for_game(game_state.game_id)

    service.get_npc_agent(game_state, npc_major)
    service.get_npc_agent(game_state, npc_minor)

    # Both caches should have triggered two creations total
    assert creation_counts["individual"] == 2
    assert puppeteer_counts["puppeteer"] == 2
