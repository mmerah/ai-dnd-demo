"""Centralized container for dependency injection."""

from functools import cached_property

from app.agents.core.types import AgentType
from app.agents.factory import AgentFactory
from app.agents.summarizer.agent import SummarizerAgent
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
from app.interfaces.services.ai import IAIService, IContextService, IEventLoggerService, IMessageService
from app.interfaces.services.character import ICharacterComputeService, ICharacterService, ILevelProgressionService
from app.interfaces.services.common import IActionService, IBroadcastService, IDiceService, IPathResolver
from app.interfaces.services.data import IItemRepository, ILoader, IMonsterRepository, ISpellRepository
from app.interfaces.services.game import (
    ICombatService,
    IConversationService,
    IEventManager,
    IGameFactory,
    IGameService,
    IGameStateManager,
    ILocationService,
    IMessageManager,
    IMetadataService,
    IMonsterFactory,
    IPreSaveSanitizer,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.scenario import ScenarioSheet
from app.services.ai import AIService, MessageService
from app.services.ai.context_service import ContextService
from app.services.ai.event_logger_service import EventLoggerService
from app.services.ai.orchestrator_service import AgentOrchestrator
from app.services.ai.tool_call_extractor_service import ToolCallExtractorService
from app.services.character import CharacterService
from app.services.character.compute_service import CharacterComputeService
from app.services.character.level_service import LevelProgressionService
from app.services.common import BroadcastService, DiceService
from app.services.common.action_service import ActionService
from app.services.common.path_resolver import PathResolver
from app.services.data.loaders.character_loader import CharacterLoader
from app.services.data.loaders.scenario_loader import ScenarioLoader
from app.services.data.repositories.alignment_repository import AlignmentRepository
from app.services.data.repositories.background_repository import BackgroundRepository
from app.services.data.repositories.class_repository import ClassRepository, SubclassRepository
from app.services.data.repositories.condition_repository import ConditionRepository
from app.services.data.repositories.damage_type_repository import DamageTypeRepository
from app.services.data.repositories.feat_repository import FeatRepository
from app.services.data.repositories.feature_repository import FeatureRepository
from app.services.data.repositories.item_repository import ItemRepository
from app.services.data.repositories.language_repository import LanguageRepository
from app.services.data.repositories.magic_school_repository import MagicSchoolRepository
from app.services.data.repositories.monster_repository import MonsterRepository
from app.services.data.repositories.race_repository import RaceRepository
from app.services.data.repositories.race_repository import SubraceRepository as RaceSubraceRepository
from app.services.data.repositories.skill_repository import SkillRepository
from app.services.data.repositories.spell_repository import SpellRepository
from app.services.data.repositories.trait_repository import TraitRepository
from app.services.data.repositories.weapon_property_repository import WeaponPropertyRepository
from app.services.game import GameService
from app.services.game.combat_service import CombatService
from app.services.game.conversation_service import ConversationService
from app.services.game.event_manager import EventManager
from app.services.game.game_factory import GameFactory
from app.services.game.game_state_manager import GameStateManager
from app.services.game.message_manager import MessageManager as GameMessageManager
from app.services.game.metadata_service import MetadataService
from app.services.game.monster_factory import MonsterFactory
from app.services.game.pre_save_sanitizer import PreSaveSanitizer
from app.services.game.save_manager import SaveManager
from app.services.scenario import ScenarioService


class Container:
    """
    Centralized container for dependency injection.
    It manages the creation and lifecycle of services and agents.
    Uses @cached_property for lazy initialization without | None pattern.
    """

    @cached_property
    def game_factory(self) -> IGameFactory:
        return GameFactory(
            scenario_service=self.scenario_service,
            compute_service=self.character_compute_service,
            location_service=self.location_service,
        )

    @cached_property
    def game_service(self) -> IGameService:
        return GameService(
            scenario_service=self.scenario_service,
            save_manager=self.save_manager,
            pre_save_sanitizer=self.pre_save_sanitizer,
            game_state_manager=self.game_state_manager,
            compute_service=self.character_compute_service,
            item_repository=self.item_repository,
            monster_factory=self.monster_factory,
            location_service=self.location_service,
            game_factory=self.game_factory,
        )

    @cached_property
    def character_service(self) -> ICharacterService:
        return CharacterService(
            path_resolver=self.path_resolver,
            character_loader=self.character_loader,
            item_repository=self.item_repository,
            spell_repository=self.spell_repository,
            alignment_repository=self.alignment_repository,
            class_repository=self.class_repository,
            subclass_repository=self.subclass_repository,
            language_repository=self.language_repository,
            condition_repository=self.condition_repository,
            race_repository=self.race_repository,
            race_subrace_repository=self.race_subrace_repository,
            background_repository=self.background_repository,
            skill_repository=self.skill_repository,
            trait_repository=self.trait_repository,
            feature_repository=self.feature_repository,
            feat_repository=self.feat_repository,
            damage_type_repository=self.damage_type_repository,
            weapon_property_repository=self.weapon_property_repository,
        )

    @cached_property
    def scenario_service(self) -> IScenarioService:
        return ScenarioService(
            path_resolver=self.path_resolver,
            scenario_loader=self.scenario_loader,
            monster_repository=self.monster_repository,
            character_service=self.character_service,
        )

    @cached_property
    def dice_service(self) -> IDiceService:
        return DiceService()

    @cached_property
    def path_resolver(self) -> IPathResolver:
        return PathResolver()

    @cached_property
    def item_repository(self) -> IItemRepository:
        return ItemRepository(self.path_resolver)

    @cached_property
    def monster_repository(self) -> IMonsterRepository:
        return MonsterRepository(
            self.path_resolver,
            language_repository=self.language_repository,
            condition_repository=self.condition_repository,
            alignment_repository=self.alignment_repository,
            skill_repository=self.skill_repository,
        )

    @cached_property
    def monster_factory(self) -> IMonsterFactory:
        return MonsterFactory()

    @cached_property
    def location_service(self) -> ILocationService:
        from app.services.game.location_service import LocationService

        return LocationService(monster_factory=self.monster_factory)

    @cached_property
    def spell_repository(self) -> ISpellRepository:
        return SpellRepository(self.path_resolver, magic_school_repository=self.magic_school_repository)

    @cached_property
    def magic_school_repository(self) -> MagicSchoolRepository:
        return MagicSchoolRepository(self.path_resolver)

    @cached_property
    def alignment_repository(self) -> AlignmentRepository:
        return AlignmentRepository(self.path_resolver)

    @cached_property
    def class_repository(self) -> ClassRepository:
        return ClassRepository(self.path_resolver)

    @cached_property
    def subclass_repository(self) -> SubclassRepository:
        return SubclassRepository(self.path_resolver)

    @cached_property
    def language_repository(self) -> LanguageRepository:
        return LanguageRepository(self.path_resolver)

    @cached_property
    def condition_repository(self) -> ConditionRepository:
        return ConditionRepository(self.path_resolver)

    @cached_property
    def race_repository(self) -> RaceRepository:
        return RaceRepository(self.path_resolver)

    @cached_property
    def race_subrace_repository(self) -> RaceSubraceRepository:
        return RaceSubraceRepository(self.path_resolver)

    @cached_property
    def background_repository(self) -> BackgroundRepository:
        return BackgroundRepository(self.path_resolver)

    @cached_property
    def trait_repository(self) -> TraitRepository:
        return TraitRepository(self.path_resolver)

    @cached_property
    def feature_repository(self) -> FeatureRepository:
        return FeatureRepository(self.path_resolver)

    @cached_property
    def feat_repository(self) -> FeatRepository:
        return FeatRepository(self.path_resolver)

    @cached_property
    def skill_repository(self) -> SkillRepository:
        return SkillRepository(self.path_resolver)

    @cached_property
    def weapon_property_repository(self) -> WeaponPropertyRepository:
        return WeaponPropertyRepository(self.path_resolver)

    @cached_property
    def damage_type_repository(self) -> DamageTypeRepository:
        return DamageTypeRepository(self.path_resolver)

    @cached_property
    def character_loader(self) -> ILoader[CharacterSheet]:
        return CharacterLoader()

    @cached_property
    def scenario_loader(self) -> ILoader[ScenarioSheet]:
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
    def character_compute_service(self) -> ICharacterComputeService:
        return CharacterComputeService(
            class_repository=self.class_repository,
            skill_repository=self.skill_repository,
            item_repository=self.item_repository,
            spell_repository=self.spell_repository,
            race_repository=self.race_repository,
        )

    @cached_property
    def level_progression_service(self) -> ILevelProgressionService:
        return LevelProgressionService(self.character_compute_service)

    @cached_property
    def event_bus(self) -> IEventBus:
        event_bus = EventBus(self.game_service)

        # Register all handlers
        event_bus.register_handler("character", CharacterHandler(self.game_service, self.level_progression_service))
        event_bus.register_handler("dice", DiceHandler(self.game_service, self.dice_service))
        event_bus.register_handler(
            "inventory", InventoryHandler(self.game_service, self.item_repository, self.character_compute_service)
        )
        event_bus.register_handler("time", TimeHandler(self.game_service))
        event_bus.register_handler("broadcast", BroadcastHandler(self.game_service, self.message_service))
        event_bus.register_handler(
            "location",
            LocationHandler(
                self.game_service,
                self.scenario_service,
                self.monster_repository,
                self.item_repository,
                self.location_service,
            ),
        )
        event_bus.register_handler(
            "combat",
            CombatHandler(
                self.game_service,
                self.scenario_service,
                self.monster_repository,
                self.combat_service,
            ),
        )
        event_bus.register_handler(
            "quest", QuestHandler(self.game_service, self.scenario_service, self.item_repository)
        )

        # Verify handlers can handle all commands
        event_bus.verify_handlers()

        return event_bus

    @cached_property
    def action_service(self) -> IActionService:
        return ActionService(
            event_bus=self.event_bus,
            event_manager=self.event_manager,
            save_manager=self.save_manager,
        )

    @cached_property
    def ai_service(self) -> IAIService:
        settings = get_settings()

        # Create narrative agent
        narrative_agent = AgentFactory.create_agent(
            AgentType.NARRATIVE,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
            metadata_service=self.metadata_service,
            message_manager=self.game_message_manager,
            event_manager=self.event_manager,
            save_manager=self.save_manager,
            conversation_service=self.conversation_service,
            context_service=self.context_service,
            event_logger_service=self.event_logger_service,
            action_service=self.action_service,
            tool_call_extractor_service=self.tool_call_extractor_service,
            debug=settings.debug_ai,
        )

        # Create combat agent
        combat_agent = AgentFactory.create_agent(
            AgentType.COMBAT,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
            metadata_service=self.metadata_service,
            message_manager=self.game_message_manager,
            event_manager=self.event_manager,
            save_manager=self.save_manager,
            conversation_service=self.conversation_service,
            context_service=self.context_service,
            event_logger_service=self.event_logger_service,
            tool_call_extractor_service=self.tool_call_extractor_service,
            action_service=self.action_service,
            debug=settings.debug_ai,
        )

        # Create summarizer agent
        summarizer_agent = AgentFactory.create_agent(
            AgentType.SUMMARIZER,
            event_bus=self.event_bus,
            scenario_service=self.scenario_service,
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
            metadata_service=self.metadata_service,
            message_manager=self.game_message_manager,
            event_manager=self.event_manager,
            save_manager=self.save_manager,
            conversation_service=self.conversation_service,
            context_service=self.context_service,
            event_logger_service=self.event_logger_service,
            action_service=self.action_service,
            tool_call_extractor_service=self.tool_call_extractor_service,
            debug=settings.debug_ai,
        )
        # The orchestrator requires a summarizer and not just a BaseAgent
        assert isinstance(summarizer_agent, SummarizerAgent)

        orchestrator = AgentOrchestrator(
            narrative_agent=narrative_agent,
            combat_agent=combat_agent,
            summarizer_agent=summarizer_agent,
            combat_service=self.combat_service,
            event_bus=self.event_bus,
            game_service=self.game_service,
        )
        return AIService(orchestrator)

    @cached_property
    def message_service(self) -> IMessageService:
        return MessageService(self.broadcast_service)

    @cached_property
    def broadcast_service(self) -> IBroadcastService:
        return BroadcastService()

    @cached_property
    def combat_service(self) -> ICombatService:
        return CombatService()

    @cached_property
    def pre_save_sanitizer(self) -> IPreSaveSanitizer:
        return PreSaveSanitizer()

    @cached_property
    def conversation_service(self) -> IConversationService:
        return ConversationService(
            message_manager=self.game_message_manager,
            metadata_service=self.metadata_service,
            save_manager=self.save_manager,
        )

    @cached_property
    def context_service(self) -> IContextService:
        return ContextService(
            item_repository=self.item_repository,
            monster_repository=self.monster_repository,
            spell_repository=self.spell_repository,
        )

    @cached_property
    def event_logger_service(self) -> IEventLoggerService:
        settings = get_settings()
        return EventLoggerService(game_id="", debug=settings.debug_ai)

    @cached_property
    def tool_call_extractor_service(self) -> ToolCallExtractorService:
        return ToolCallExtractorService(event_bus=self.event_bus)


# Singleton instance of the container
container = Container()
