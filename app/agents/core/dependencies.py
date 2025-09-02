"""Agent dependencies for tool context."""

from dataclasses import dataclass

from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IGameService,
    IItemRepository,
    IMonsterRepository,
    IScenarioService,
    ISpellRepository,
)
from app.models.game_state import GameState


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    game_service: IGameService
    event_bus: IEventBus
    scenario_service: IScenarioService
    item_repository: IItemRepository
    monster_repository: IMonsterRepository
    spell_repository: ISpellRepository
