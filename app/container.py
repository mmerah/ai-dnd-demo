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
    IEventManager,
    IGameService,
    IGameStateManager,
    IItemRepository,
    ILoader,
    IMessageManager,
    IMessageService,
    IMetadataService,
    IMonsterRepository,
    IPathResolver,
    ISaveManager,
    IScenarioService,
    ISpellRepository,
)
from app.models.character import CharacterSheet
from app.models.scenario import Scenario
from app.services.ai import AIService, MessageService
from app.services.character import CharacterService
from app.services.common import BroadcastService, DiceService
from app.services.common.path_resolver import PathResolver
from app.services.data.loaders.character_loader import CharacterLoader
from app.services.data.loaders.scenario_loader import ScenarioLoader
from app.services.data.repositories.item_repository import ItemRepository
from app.services.data.repositories.monster_repository import MonsterRepository
from app.services.data.repositories.spell_repository import SpellRepository
from app.services.game import GameService
from app.services.game.event_manager import EventManager
from app.services.game.game_state_manager import GameStateManager
from app.services.game.message_manager import MessageManager as GameMessageManager
from app.services.game.metadata_service import MetadataService
from app.services.game.save_manager import SaveManager
from app.services.scenario import ScenarioService


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
        self._path_resolver: IPathResolver | None = None
        self._item_repository: IItemRepository | None = None
        self._monster_repository: IMonsterRepository | None = None
        self._spell_repository: ISpellRepository | None = None
        self._character_loader: ILoader[CharacterSheet] | None = None
        self._scenario_loader: ILoader[Scenario] | None = None
        self._save_manager: ISaveManager | None = None
        self._game_state_manager: IGameStateManager | None = None
        self._game_message_manager: IMessageManager | None = None
        self._event_manager: IEventManager | None = None
        self._metadata_service: IMetadataService | None = None
        self._event_bus: IEventBus | None = None
        self._ai_service: IAIService | None = None
        self._message_service: IMessageService | None = None
        self._broadcast_service: IBroadcastService | None = None

    def get_game_service(self) -> IGameService:
        if self._game_service is None:
            scenario_service = self.get_scenario_service()
            save_manager = self.get_save_manager()
            game_state_manager = self.get_game_state_manager()
            message_manager = self.get_game_message_manager()
            event_manager = self.get_event_manager()
            metadata_service = self.get_metadata_service()
            self._game_service = GameService(
                scenario_service=scenario_service,
                save_manager=save_manager,
                game_state_manager=game_state_manager,
                message_manager=message_manager,
                event_manager=event_manager,
                metadata_service=metadata_service,
            )
        return self._game_service

    def get_character_service(self) -> ICharacterService:
        if self._character_service is None:
            path_resolver = self.get_path_resolver()
            character_loader = self.get_character_loader()
            item_repository = self.get_item_repository()
            spell_repository = self.get_spell_repository()
            self._character_service = CharacterService(
                path_resolver=path_resolver,
                character_loader=character_loader,
                item_repository=item_repository,
                spell_repository=spell_repository,
            )
        return self._character_service

    def get_scenario_service(self) -> IScenarioService:
        if self._scenario_service is None:
            path_resolver = self.get_path_resolver()
            scenario_loader = self.get_scenario_loader()
            monster_repository = self.get_monster_repository()
            self._scenario_service = ScenarioService(
                path_resolver=path_resolver,
                scenario_loader=scenario_loader,
                monster_repository=monster_repository,
            )
        return self._scenario_service

    def get_dice_service(self) -> DiceService:
        if self._dice_service is None:
            self._dice_service = DiceService()
        return self._dice_service

    def get_path_resolver(self) -> IPathResolver:
        if self._path_resolver is None:
            self._path_resolver = PathResolver()
        return self._path_resolver

    def get_item_repository(self) -> IItemRepository:
        if self._item_repository is None:
            path_resolver = self.get_path_resolver()
            self._item_repository = ItemRepository(path_resolver)
        return self._item_repository

    def get_monster_repository(self) -> IMonsterRepository:
        if self._monster_repository is None:
            path_resolver = self.get_path_resolver()
            self._monster_repository = MonsterRepository(path_resolver)
        return self._monster_repository

    def get_spell_repository(self) -> ISpellRepository:
        if self._spell_repository is None:
            path_resolver = self.get_path_resolver()
            self._spell_repository = SpellRepository(path_resolver)
        return self._spell_repository

    def get_character_loader(self) -> ILoader[CharacterSheet]:
        if self._character_loader is None:
            self._character_loader = CharacterLoader()
        return self._character_loader

    def get_scenario_loader(self) -> ILoader[Scenario]:
        if self._scenario_loader is None:
            path_resolver = self.get_path_resolver()
            self._scenario_loader = ScenarioLoader(path_resolver)
        return self._scenario_loader

    def get_save_manager(self) -> ISaveManager:
        if self._save_manager is None:
            path_resolver = self.get_path_resolver()
            self._save_manager = SaveManager(path_resolver)
        return self._save_manager

    def get_game_state_manager(self) -> IGameStateManager:
        if self._game_state_manager is None:
            self._game_state_manager = GameStateManager()
        return self._game_state_manager

    def get_game_message_manager(self) -> IMessageManager:
        if self._game_message_manager is None:
            self._game_message_manager = GameMessageManager()
        return self._game_message_manager

    def get_event_manager(self) -> IEventManager:
        if self._event_manager is None:
            self._event_manager = EventManager()
        return self._event_manager

    def get_metadata_service(self) -> IMetadataService:
        if self._metadata_service is None:
            self._metadata_service = MetadataService()
        return self._metadata_service

    def get_event_bus(self) -> IEventBus:
        if self._event_bus is None:
            game_service = self.get_game_service()
            dice_service = self.get_dice_service()
            scenario_service = self.get_scenario_service()
            message_service = self.get_message_service()
            monster_repository = self.get_monster_repository()
            item_repository = self.get_item_repository()

            event_bus = EventBus(game_service)

            # Register all handlers
            event_bus.register_handler("character", CharacterHandler(game_service))
            event_bus.register_handler("dice", DiceHandler(game_service, dice_service))
            event_bus.register_handler("inventory", InventoryHandler(game_service))
            event_bus.register_handler("time", TimeHandler(game_service))
            event_bus.register_handler("broadcast", BroadcastHandler(game_service, message_service))
            event_bus.register_handler(
                "location", LocationHandler(game_service, scenario_service, monster_repository, item_repository)
            )
            event_bus.register_handler("combat", CombatHandler(game_service, scenario_service, monster_repository))
            event_bus.register_handler("quest", QuestHandler(game_service, scenario_service, item_repository))

            self._event_bus = event_bus
        return self._event_bus

    def get_ai_service(self) -> IAIService:
        if self._ai_service is None:
            settings = get_settings()
            event_bus = self.get_event_bus()
            game_service = self.get_game_service()
            scenario_service = self.get_scenario_service()
            item_repository = self.get_item_repository()
            monster_repository = self.get_monster_repository()
            spell_repository = self.get_spell_repository()

            ai_service = AIService(game_service)
            ai_service.narrative_agent = AgentFactory.create_agent(
                AgentType.NARRATIVE,
                event_bus=event_bus,
                scenario_service=scenario_service,
                item_repository=item_repository,
                monster_repository=monster_repository,
                spell_repository=spell_repository,
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
