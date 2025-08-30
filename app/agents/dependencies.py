"""Agent dependencies for tool context."""

from dataclasses import dataclass

from app.interfaces.events import IEventBus
from app.interfaces.services import IDataService, IGameService, IScenarioService
from app.models.game_state import GameState


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    game_service: IGameService
    event_bus: IEventBus
    scenario_service: IScenarioService
    data_service: IDataService
