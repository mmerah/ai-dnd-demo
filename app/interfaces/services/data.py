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
    def validate_reference(self, key: str) -> bool:
        """Check if a reference exists.

        Args:
            key: The key to validate

        Returns:
            True if the key exists, False otherwise
        """
        pass

    @abstractmethod
    def get_name_from_index(self, index: str) -> str | None:
        """Resolve canonical name from an index/key (case-insensitive).

        Searches for the item by index/key and returns its display name.
        Performs case-insensitive matching.

        Args:
            index: The index/key to resolve

        Returns:
            The item's display name if found, None otherwise
        """
        pass


class IItemRepository(IRepository[ItemDefinition]):
    """Repository interface for item data."""

    @abstractmethod
    def get_by_type(self, item_type: ItemType) -> list[ItemDefinition]:
        """Get all items of a specific type.

        Args:
            item_type: Type of items to retrieve (WEAPON, ARMOR, etc.)

        Returns:
            List of items matching the specified type
        """
        pass

    @abstractmethod
    def get_by_rarity(self, rarity: ItemRarity) -> list[ItemDefinition]:
        """Get all items of a specific rarity.

        Args:
            rarity: Rarity level to filter by

        Returns:
            List of items matching the specified rarity
        """
        pass


class IMonsterRepository(IRepository[MonsterSheet]):
    """Repository interface for monster data."""

    @abstractmethod
    def get_by_challenge_rating(self, min_cr: float, max_cr: float) -> list[MonsterSheet]:
        """Get all monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating (inclusive)
            max_cr: Maximum challenge rating (inclusive)

        Returns:
            List of monsters with CR in the specified range
        """
        pass

    @abstractmethod
    def get_by_type(self, creature_type: str) -> list[MonsterSheet]:
        """Get all monsters of a specific type.

        Args:
            creature_type: Type of creature (humanoid, beast, undead, etc.)

        Returns:
            List of monsters matching the specified type
        """
        pass


class ISpellRepository(IRepository[SpellDefinition]):
    """Repository interface for spell data."""

    @abstractmethod
    def get_by_level(self, level: int) -> list[SpellDefinition]:
        """Get all spells of a specific level.

        Args:
            level: Spell level (0 for cantrips, 1-9 for leveled spells)

        Returns:
            List of spells of the specified level
        """
        pass

    @abstractmethod
    def get_by_school(self, school: SpellSchool) -> list[SpellDefinition]:
        """Get all spells of a specific school.

        Args:
            school: School of magic (evocation, illusion, etc.)

        Returns:
            List of spells from the specified school
        """
        pass

    @abstractmethod
    def get_by_class(self, class_name: str) -> list[SpellDefinition]:
        """Get all spells available to a specific class.

        Args:
            class_name: Name of the class (wizard, cleric, etc.)

        Returns:
            List of spells available to the specified class
        """
        pass
