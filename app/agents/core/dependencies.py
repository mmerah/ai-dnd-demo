"""Agent dependencies for tool context."""

from dataclasses import dataclass

from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IEventManager,
    IItemRepository,
    IMessageManager,
    IMetadataService,
    IMonsterRepository,
    ISaveManager,
    IScenarioService,
    ISpellRepository,
)
from app.models.game_state import GameState


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    event_bus: IEventBus
    scenario_service: IScenarioService
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
    message_manager: IMessageManager
    event_manager: IEventManager
    metadata_service: IMetadataService
    save_manager: ISaveManager
