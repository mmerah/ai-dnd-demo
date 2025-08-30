"""Centralized container for dependency injection."""

from app.agents.factory import AgentFactory
from app.agents.types import AgentType
from app.config import get_settings
from app.events.event_bus import EventBus
from app.events.handlers.broadcast_handler import BroadcastHandler
from app.events.handlers.character_handler import CharacterHandler
from app.events.handlers.combat_handler import CombatHandler
from app.events.handlers.dice_handler import DiceHandler
from app.events.handlers.inventory_handler import InventoryHandler
from app.events.handlers.location_handler import LocationHandler
from app.events.handlers.quest_handler import QuestHandler
from app.events.handlers.time_handler import TimeHandler
from app.interfaces.events import IEventBus
from app.interfaces.services import (
    IAIService,
    IBroadcastService,
    ICharacterService,
    IDataService,
    IGameService,
    IMessageService,
    IScenarioService,
)
from app.services.ai_service import AIService
from app.services.broadcast_service import BroadcastService
from app.services.character_service import CharacterService
from app.services.data_service import DataService
from app.services.dice_service import DiceService
from app.services.game_service import GameService
from app.services.message_service import MessageService
from app.services.scenario_service import ScenarioService


class Container:
    """
    Centralized container for dependency injection.
    It manages the creation and lifecycle of services and agents.
    """

    def __init__(self) -> None:
        self._game_service: IGameService | None = None
        self._character_service: ICharacterService | None = None
        self._scenario_service: IScenarioService | None = None
        self._dice_service: DiceService | None = None
        self._data_service: IDataService | None = None
        self._event_bus: IEventBus | None = None
        self._ai_service: IAIService | None = None
        self._message_service: IMessageService | None = None
        self._broadcast_service: IBroadcastService | None = None

    def get_game_service(self) -> IGameService:
        if self._game_service is None:
            self._game_service = GameService()
        return self._game_service

    def get_character_service(self) -> ICharacterService:
        if self._character_service is None:
            data_service = self.get_data_service()
            self._character_service = CharacterService(data_service=data_service)
        return self._character_service

    def get_scenario_service(self) -> IScenarioService:
        if self._scenario_service is None:
            data_service = self.get_data_service()
            self._scenario_service = ScenarioService(data_service=data_service)
        return self._scenario_service

    def get_dice_service(self) -> DiceService:
        if self._dice_service is None:
            self._dice_service = DiceService()
        return self._dice_service

    def get_data_service(self) -> IDataService:
        if self._data_service is None:
            self._data_service = DataService()
        return self._data_service

    def get_event_bus(self) -> IEventBus:
        if self._event_bus is None:
            game_service = self.get_game_service()
            dice_service = self.get_dice_service()
            scenario_service = self.get_scenario_service()
            data_service = self.get_data_service()
            message_service = self.get_message_service()

            event_bus = EventBus(game_service)

            # Register all handlers
            event_bus.register_handler("character", CharacterHandler(game_service))
            event_bus.register_handler("dice", DiceHandler(game_service, dice_service))
            event_bus.register_handler("inventory", InventoryHandler(game_service))
            event_bus.register_handler("time", TimeHandler(game_service))
            event_bus.register_handler("broadcast", BroadcastHandler(game_service, message_service))
            event_bus.register_handler("location", LocationHandler(game_service, scenario_service, data_service))
            event_bus.register_handler("combat", CombatHandler(game_service, scenario_service, data_service))
            event_bus.register_handler("quest", QuestHandler(game_service, scenario_service, data_service))

            self._event_bus = event_bus
        return self._event_bus

    def get_ai_service(self) -> IAIService:
        if self._ai_service is None:
            settings = get_settings()
            event_bus = self.get_event_bus()
            game_service = self.get_game_service()
            scenario_service = self.get_scenario_service()
            data_service = self.get_data_service()

            ai_service = AIService(game_service)
            ai_service.narrative_agent = AgentFactory.create_agent(
                AgentType.NARRATIVE,
                event_bus=event_bus,
                scenario_service=scenario_service,
                data_service=data_service,
                debug=settings.debug_ai,
            )
            self._ai_service = ai_service
        return self._ai_service

    def get_message_service(self) -> IMessageService:
        if self._message_service is None:
            broadcast_service = self.get_broadcast_service()
            self._message_service = MessageService(broadcast_service)
        return self._message_service

    def get_broadcast_service(self) -> IBroadcastService:
        if self._broadcast_service is None:
            self._broadcast_service = BroadcastService()
        return self._broadcast_service


# Singleton instance of the container
container = Container()
