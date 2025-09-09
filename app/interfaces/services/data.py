from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from app.models.item import ItemDefinition, ItemRarity, ItemType
from app.models.monster import MonsterSheet
from app.models.spell import SpellDefinition, SpellSchool

# Type variable for generic interfaces
T = TypeVar("T")


class ILoader(ABC, Generic[T]):
    """Base interface for data loaders."""

    @abstractmethod
    def load(self, path: Path) -> T:
        """Load data from a file."""
        pass


class IRepository(ABC, Generic[T]):
    """Base interface for data repositories."""

    @abstractmethod
    def get(self, key: str) -> T:
        """Get an item by its key. Raises RepositoryNotFoundError if not found."""
        pass

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all available keys."""
        pass

    @abstractmethod
    def validate_reference(self, key: str) -> bool:
        """Check if a reference exists."""
        pass

    @abstractmethod
    def get_name_from_index(self, index: str) -> str | None:
        """Resolve canonical name from an index/key (case-insensitive)."""
        pass


class IItemRepository(IRepository[ItemDefinition]):
    """Repository interface for item data."""

    @abstractmethod
    def get_by_type(self, item_type: ItemType) -> list[ItemDefinition]:
        """Get all items of a specific type."""
        pass

    @abstractmethod
    def get_by_rarity(self, rarity: ItemRarity) -> list[ItemDefinition]:
        """Get all items of a specific rarity."""
        pass


class IMonsterRepository(IRepository[MonsterSheet]):
    """Repository interface for monster data."""

    @abstractmethod
    def get_by_challenge_rating(self, min_cr: float, max_cr: float) -> list[MonsterSheet]:
        """Get all monsters within a challenge rating range."""
        pass

    @abstractmethod
    def get_by_type(self, creature_type: str) -> list[MonsterSheet]:
        """Get all monsters of a specific type."""
        pass


class ISpellRepository(IRepository[SpellDefinition]):
    """Repository interface for spell data."""

    @abstractmethod
    def get_by_level(self, level: int) -> list[SpellDefinition]:
        """Get all spells of a specific level."""
        pass

    @abstractmethod
    def get_by_school(self, school: SpellSchool) -> list[SpellDefinition]:
        """Get all spells of a specific school."""
        pass

    @abstractmethod
    def get_by_class(self, class_name: str) -> list[SpellDefinition]:
        """Get all spells available to a specific class."""
        pass
