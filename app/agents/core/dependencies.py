"""Agent dependencies for tool context."""

from dataclasses import dataclass

from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IItemRepository, IMonsterRepository, ISpellRepository
from app.interfaces.services.game import IEventManager, IMessageManager, IMetadataService, ISaveManager
from app.interfaces.services.scenario import IScenarioService
from app.models.game_state import GameState


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    event_bus: IEventBus
    agent_type: AgentType
    scenario_service: IScenarioService
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
    message_manager: IMessageManager
    event_manager: IEventManager
    metadata_service: IMetadataService
    save_manager: ISaveManager
    action_service: IActionService
