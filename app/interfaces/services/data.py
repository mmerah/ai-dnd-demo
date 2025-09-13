from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Generic, TypeVar

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

# Type variable for generic interfaces
T = TypeVar("T")


class ILoader(ABC, Generic[T]):
    """Base interface for data loaders."""

    @abstractmethod
    def load(self, path: Path) -> T:
        """Load data from a file.

        Args:
            path: Path to the file to load

        Returns:
            Loaded data object

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file content is invalid
        """
        pass


class IRepository(ABC, Generic[T]):
    """Base interface for data repositories."""

    @abstractmethod
    def get(self, key: str) -> T:
        """Get an item by its key.

        Args:
            key: The key/index to look up

        Returns:
            The item if found

        Raises:
            RepositoryNotFoundError: If the item is not found
        """
        pass

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all available keys.

        Returns:
            Sorted list of all keys in the repository
        """
        pass

    @abstractmethod
    def get_name(self, key: str) -> str:
        """Get the display name for a given key.

        Args:
            key: The key/index to look up

        Returns:
            The display name, or formatted key as fallback

        """
        pass

    @abstractmethod
    def validate_reference(self, key: str) -> bool:
        """Check if a reference exists.

        Args:
            key: The key to validate

        Returns:
            True if the key exists, False otherwise
        """
        pass

    @abstractmethod
    def get_item_pack_id(self, key: str) -> str | None:
        """Return the content pack id that provided this key, if known.

        Repositories that load from multiple content packs can track which pack
        contributed each item when caching is enabled. When unknown, returns None.

        Args:
            key: The key/index to look up

        Returns:
            Pack id string or None if unavailable
        """
        pass

    @abstractmethod
    def filter(self, *predicates: Callable[[T], bool]) -> list[T]:
        """Filter repository items using one or more predicate functions.

        All predicates must return True for an item to be included (AND logic).

        Examples:
            # Single filter
            weapons = item_repo.filter(lambda item: item.type == ItemType.WEAPON)

            # Multiple filters (AND logic)
            cheap_weapons = item_repo.filter(
                lambda item: item.type == ItemType.WEAPON,
                lambda item: item.value < 50
            )

            # Complex filter with OR logic inside predicate
            magic_or_rare = item_repo.filter(
                lambda item: item.rarity == ItemRarity.RARE or "magic" in item.properties
            )

        Args:
            *predicates: One or more functions that return True for items to include

        Returns:
            List of items matching all predicates
        """
        pass


class IRepositoryProvider(ABC):
    """Provider interface for pack-scoped repositories."""

    @abstractmethod
    def get_item_repository_for(self, game_state: GameState) -> IRepository[ItemDefinition]:
        """Get an item repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_monster_repository_for(self, game_state: GameState) -> IRepository[MonsterSheet]:
        """Get a monster repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_spell_repository_for(self, game_state: GameState) -> IRepository[SpellDefinition]:
        """Get a spell repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_magic_school_repository_for(self, game_state: GameState) -> IRepository[MagicSchool]:
        """Get a magic school repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_alignment_repository_for(self, game_state: GameState) -> IRepository[Alignment]:
        """Get an alignment repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_condition_repository_for(self, game_state: GameState) -> IRepository[Condition]:
        """Get a condition repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_language_repository_for(self, game_state: GameState) -> IRepository[Language]:
        """Get a language repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_skill_repository_for(self, game_state: GameState) -> IRepository[Skill]:
        """Get a skill repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_class_repository_for(self, game_state: GameState) -> IRepository[ClassDefinition]:
        """Get a class repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_subclass_repository_for(self, game_state: GameState) -> IRepository[SubclassDefinition]:
        """Get a subclass repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_race_repository_for(self, game_state: GameState) -> IRepository[RaceDefinition]:
        """Get a race repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_race_subrace_repository_for(self, game_state: GameState) -> IRepository[RaceSubraceDefinition]:
        """Get a race subrace repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_background_repository_for(self, game_state: GameState) -> IRepository[BackgroundDefinition]:
        """Get a background repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_trait_repository_for(self, game_state: GameState) -> IRepository[TraitDefinition]:
        """Get a trait repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_feature_repository_for(self, game_state: GameState) -> IRepository[FeatureDefinition]:
        """Get a feature repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_feat_repository_for(self, game_state: GameState) -> IRepository[FeatDefinition]:
        """Get a feat repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_damage_type_repository_for(self, game_state: GameState) -> IRepository[DamageType]:
        """Get a damage type repository scoped to the game's content packs."""
        pass

    @abstractmethod
    def get_weapon_property_repository_for(self, game_state: GameState) -> IRepository[WeaponProperty]:
        """Get a weapon property repository scoped to the game's content packs."""
        pass
