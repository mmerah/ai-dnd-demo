"""Factory for creating per-game, pack-scoped repositories."""

from __future__ import annotations

from dataclasses import dataclass

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.interfaces.services.data import IRepository, IRepositoryProvider
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.condition import Condition
from app.models.damage_type import DamageType
from app.models.feat import FeatDefinition
from app.models.feature import FeatureDefinition
from app.models.game_state import GameState
from app.models.item import ItemDefinition
from app.models.language import Language
from app.models.magic_school import MagicSchool
from app.models.monster import MonsterSheet
from app.models.race import RaceDefinition
from app.models.race import SubraceDefinition as RaceSubraceDefinition
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition
from app.models.weapon_property import WeaponProperty
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


@dataclass
class GameRepositoryScope:
    """Pack-scoped repositories for a specific game."""

    # Core catalogs used at runtime
    item_repository: IRepository[ItemDefinition]
    monster_repository: IRepository[MonsterSheet]
    spell_repository: IRepository[SpellDefinition]

    # Dependencies used by the above
    magic_school_repository: IRepository[MagicSchool]
    alignment_repository: IRepository[Alignment]
    condition_repository: IRepository[Condition]
    language_repository: IRepository[Language]
    skill_repository: IRepository[Skill]
    class_repository: IRepository[ClassDefinition]
    race_repository: IRepository[RaceDefinition]
    subclass_repository: IRepository[SubclassDefinition]
    race_subrace_repository: IRepository[RaceSubraceDefinition]
    background_repository: IRepository[BackgroundDefinition]
    trait_repository: IRepository[TraitDefinition]
    feature_repository: IRepository[FeatureDefinition]
    feat_repository: IRepository[FeatDefinition]
    damage_type_repository: IRepository[DamageType]
    weapon_property_repository: IRepository[WeaponProperty]


class RepositoryFactory(IRepositoryProvider):
    """Creates repositories limited to a set of content packs."""

    def __init__(self, path_resolver: IPathResolver, content_pack_registry: IContentPackRegistry) -> None:
        self.path_resolver = path_resolver
        self.content_pack_registry = content_pack_registry
        self._repository_cache: dict[tuple[str, ...], GameRepositoryScope] = {}

    def create_scope(self, content_packs: list[str]) -> GameRepositoryScope:
        # Dependencies first
        magic_school_repo = MagicSchoolRepository(
            self.path_resolver,
            content_pack_registry=self.content_pack_registry,
            content_packs=content_packs,
        )
        alignment_repo = AlignmentRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        condition_repo = ConditionRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        language_repo = LanguageRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        skill_repo = SkillRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        class_repo = ClassRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        subclass_repo = SubclassRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        race_repo = RaceRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        subrace_repo = RaceSubraceRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        background_repo = BackgroundRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        trait_repo = TraitRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        feature_repo = FeatureRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        feat_repo = FeatRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        damage_type_repo = DamageTypeRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )
        weapon_prop_repo = WeaponPropertyRepository(
            self.path_resolver, content_pack_registry=self.content_pack_registry, content_packs=content_packs
        )

        # Core repos
        item_repo = ItemRepository(
            self.path_resolver,
            content_pack_registry=self.content_pack_registry,
            content_packs=content_packs,
        )
        spell_repo = SpellRepository(
            self.path_resolver,
            magic_school_repository=magic_school_repo,
            content_pack_registry=self.content_pack_registry,
            content_packs=content_packs,
        )
        monster_repo = MonsterRepository(
            self.path_resolver,
            language_repository=language_repo,
            condition_repository=condition_repo,
            alignment_repository=alignment_repo,
            skill_repository=skill_repo,
            content_pack_registry=self.content_pack_registry,
            content_packs=content_packs,
        )

        return GameRepositoryScope(
            item_repository=item_repo,
            monster_repository=monster_repo,
            spell_repository=spell_repo,
            magic_school_repository=magic_school_repo,
            alignment_repository=alignment_repo,
            condition_repository=condition_repo,
            language_repository=language_repo,
            skill_repository=skill_repo,
            class_repository=class_repo,
            race_repository=race_repo,
            subclass_repository=subclass_repo,
            race_subrace_repository=subrace_repo,
            background_repository=background_repo,
            trait_repository=trait_repo,
            feature_repository=feature_repo,
            feat_repository=feat_repo,
            damage_type_repository=damage_type_repo,
            weapon_property_repository=weapon_prop_repo,
        )

    def _get_or_create_scope(self, game_state: GameState) -> GameRepositoryScope:
        """Get or create a repository scope for the game's content packs.

        Uses caching to avoid recreating repository instances for the same
        set of content packs.

        Args:
            game_state: Game state containing content pack configuration

        Returns:
            GameRepositoryScope with pack-scoped repositories
        """
        # Create a cache key from the sorted content packs
        cache_key = tuple(sorted(game_state.content_packs))

        if cache_key not in self._repository_cache:
            self._repository_cache[cache_key] = self.create_scope(list(game_state.content_packs))

        return self._repository_cache[cache_key]

    def get_item_repository_for(self, game_state: GameState) -> IRepository[ItemDefinition]:
        """Get an item repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).item_repository

    def get_monster_repository_for(self, game_state: GameState) -> IRepository[MonsterSheet]:
        """Get a monster repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).monster_repository

    def get_spell_repository_for(self, game_state: GameState) -> IRepository[SpellDefinition]:
        """Get a spell repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).spell_repository

    def get_magic_school_repository_for(self, game_state: GameState) -> IRepository[MagicSchool]:
        """Get a magic school repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).magic_school_repository

    def get_alignment_repository_for(self, game_state: GameState) -> IRepository[Alignment]:
        """Get an alignment repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).alignment_repository

    def get_condition_repository_for(self, game_state: GameState) -> IRepository[Condition]:
        """Get a condition repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).condition_repository

    def get_language_repository_for(self, game_state: GameState) -> IRepository[Language]:
        """Get a language repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).language_repository

    def get_skill_repository_for(self, game_state: GameState) -> IRepository[Skill]:
        """Get a skill repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).skill_repository

    def get_class_repository_for(self, game_state: GameState) -> IRepository[ClassDefinition]:
        """Get a class repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).class_repository

    def get_subclass_repository_for(self, game_state: GameState) -> IRepository[SubclassDefinition]:
        """Get a subclass repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).subclass_repository

    def get_race_repository_for(self, game_state: GameState) -> IRepository[RaceDefinition]:
        """Get a race repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).race_repository

    def get_race_subrace_repository_for(self, game_state: GameState) -> IRepository[RaceSubraceDefinition]:
        """Get a race subrace repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).race_subrace_repository

    def get_background_repository_for(self, game_state: GameState) -> IRepository[BackgroundDefinition]:
        """Get a background repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).background_repository

    def get_trait_repository_for(self, game_state: GameState) -> IRepository[TraitDefinition]:
        """Get a trait repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).trait_repository

    def get_feature_repository_for(self, game_state: GameState) -> IRepository[FeatureDefinition]:
        """Get a feature repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).feature_repository

    def get_feat_repository_for(self, game_state: GameState) -> IRepository[FeatDefinition]:
        """Get a feat repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).feat_repository

    def get_damage_type_repository_for(self, game_state: GameState) -> IRepository[DamageType]:
        """Get a damage type repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).damage_type_repository

    def get_weapon_property_repository_for(self, game_state: GameState) -> IRepository[WeaponProperty]:
        """Get a weapon property repository scoped to the game's content packs."""
        return self._get_or_create_scope(game_state).weapon_property_repository
