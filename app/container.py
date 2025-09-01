"""Centralized container for dependency injection."""

from functools import cached_property

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
    Uses @cached_property for lazy initialization without | None pattern.
    """

    @cached_property
    def game_service(self) -> IGameService:
        return GameService(
            scenario_service=self.scenario_service,
            save_manager=self.save_manager,
            game_state_manager=self.game_state_manager,
            message_manager=self.game_message_manager,
            event_manager=self.event_manager,
            metadata_service=self.metadata_service,
        )

    @cached_property
    def character_service(self) -> ICharacterService:
        return CharacterService(
            path_resolver=self.path_resolver,
            character_loader=self.character_loader,
            item_repository=self.item_repository,
            spell_repository=self.spell_repository,
        )

    @cached_property
    def scenario_service(self) -> IScenarioService:
        return ScenarioService(
            path_resolver=self.path_resolver,
            scenario_loader=self.scenario_loader,
            monster_repository=self.monster_repository,
        )

    @cached_property
    def dice_service(self) -> DiceService:
        return DiceService()

    @cached_property
    def path_resolver(self) -> IPathResolver:
        return PathResolver()

    @cached_property
    def item_repository(self) -> IItemRepository:
        return ItemRepository(self.path_resolver)

    @cached_property
    def monster_repository(self) -> IMonsterRepository:
        return MonsterRepository(self.path_resolver)

    @cached_property
    def spell_repository(self) -> ISpellRepository:
        return SpellRepository(self.path_resolver)

    @cached_property
    def character_loader(self) -> ILoader[CharacterSheet]:
        return CharacterLoader()

    @cached_property
    def scenario_loader(self) -> ILoader[Scenario]:
        return ScenarioLoader(self.path_resolver)

    @cached_property
    def save_manager(self) -> ISaveManager:
        return SaveManager(self.path_resolver)

    @cached_property
    def game_state_manager(self) -> IGameStateManager:
        return GameStateManager()

    @cached_property
    def game_message_manager(self) -> IMessageManager:
        return GameMessageManager()

    @cached_property
    def event_manager(self) -> IEventManager:
        return EventManager()

    @cached_property
    def metadata_service(self) -> IMetadataService:
        return MetadataService()

    @cached_property
    def event_bus(self) -> IEventBus:
        event_bus = EventBus(self.game_service)

        # Register all handlers
        event_bus.register_handler("character", CharacterHandler(self.game_service))
        event_bus.register_handler("dice", DiceHandler(self.game_service, self.dice_service))
        event_bus.register_handler("inventory", InventoryHandler(self.game_service))
        event_bus.register_handler("time", TimeHandler(self.game_service))
        event_bus.register_handler("broadcast", BroadcastHandler(self.game_service, self.message_service))
        event_bus.register_handler(
            "location",
            LocationHandler(self.game_service, self.scenario_service, self.monster_repository, self.item_repository),
        )
        event_bus.register_handler(
            "combat", CombatHandler(self.game_service, self.scenario_service, self.monster_repository)
        )
        event_bus.register_handler(
            "quest", QuestHandler(self.game_service, self.scenario_service, self.item_repository)
        )

        return event_bus

    @cached_property
    def ai_service(self) -> IAIService:
        settings = get_settings()
        narrative_agent = AgentFactory.create_agent(
            AgentType.NARRATIVE,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
            metadata_service=self.metadata_service,
            debug=settings.debug_ai,
        )
        return AIService(self.game_service, narrative_agent)

    @cached_property
    def message_service(self) -> IMessageService:
        return MessageService(self.broadcast_service)

    @cached_property
    def broadcast_service(self) -> IBroadcastService:
        return BroadcastService()


# Singleton instance of the container
container = Container()
