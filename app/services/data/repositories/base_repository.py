"""Base repository pattern for data access."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, cast

from pydantic import BaseModel

from app.interfaces.services.data import IRepository


class NamedModel(Protocol):
    """Protocol for models that have a name attribute.

    All repository items (ItemDefinition, MonsterSheet, SpellDefinition)
    must implement this protocol.
    """

    name: str


# Repository items must be Pydantic models
T = TypeVar("T", bound=BaseModel)


class BaseRepository(IRepository[T], ABC, Generic[T]):
    """Abstract base class for repositories following SOLID principles.

    Provides common functionality for caching, loading, and error handling.
    """

    def __init__(self, cache_enabled: bool = True):
        """Initialize the base repository.

        Args:
            cache_enabled: Whether to cache loaded data in memory
        """
        self.cache_enabled = cache_enabled
        self._cache: dict[str, T] = {}
        self._initialized = False

    def get(self, key: str) -> T | None:
        """Get an item by its key.

        Args:
            key: The key to look up

        Returns:
            The item if found, None otherwise
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled and key in self._cache:
            return self._cache[key]

        item = self._load_item(key)
        if item and self.cache_enabled:
            self._cache[key] = item

        return item

    def list_keys(self) -> list[str]:
        """List all available keys.

        Returns:
            Sorted list of all keys
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return sorted(self._cache.keys())

        return self._get_all_keys()

    def validate_reference(self, key: str) -> bool:
        """Check if a reference exists.

        Args:
            key: The key to validate

        Returns:
            True if the key exists, False otherwise
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return key in self._cache

        return self._check_key_exists(key)

    def _extract_name(self, item: T) -> str:
        """Extract name from a repository item.

        All repository items must have a 'name' attribute by contract.
        This helper method provides type-safe access.
        """
        if not hasattr(item, "name"):
            raise AttributeError(f"Repository item {type(item).__name__} must have 'name' attribute")
        return cast(NamedModel, item).name

    def get_name_from_index(self, index: str) -> str | None:
        """Resolve canonical name from an index/key (case-insensitive).

        Default implementation for repositories. Searches cache first,
        then falls back to loading the item to get its name attribute.

        Args:
            index: The index/key to resolve

        Returns:
            The item's display name if found, None otherwise
        """
        if not self._initialized:
            self._initialize()

        key_lower = index.lower()

        # Try cache first (case-insensitive search)
        if self.cache_enabled and self._cache:
            # Direct hit
            if index in self._cache:
                item = self._cache[index]
                return self._extract_name(item)

            # Case-insensitive search
            for k, v in self._cache.items():
                item_name = self._extract_name(v)
                if k.lower() == key_lower or item_name.lower() == key_lower:
                    return item_name

        # Fallback: try to load the item
        loaded_item = self.get(index)
        if loaded_item is not None:
            return self._extract_name(loaded_item)

        # Last resort: case-insensitive key search
        for key in self.list_keys():
            if key.lower() == key_lower:
                key_item = self.get(key)
                if key_item is not None:
                    return self._extract_name(key_item)

        return None

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the repository, loading data if cache is enabled."""
        pass

    @abstractmethod
    def _load_item(self, key: str) -> T | None:
        """Load a single item by key.

        Args:
            key: The key to load

        Returns:
            The loaded item or None if not found
        """
        pass

    @abstractmethod
    def _get_all_keys(self) -> list[str]:
        """Get all available keys without using cache.

        Returns:
            List of all keys
        """
        pass

    @abstractmethod
    def _check_key_exists(self, key: str) -> bool:
        """Check if a key exists without using cache.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        pass

    def _load_json_file(self, path: Path) -> dict[str, Any] | list[Any] | None:
        # Any is necessary here because JSON can contain mixed types (strings, numbers, booleans, nested objects)
        """Helper method to load JSON from a file.

        Args:
            path: Path to the JSON file

        Returns:
            Parsed JSON data or None if file doesn't exist

        Raises:
            RuntimeError: If JSON parsing fails
        """
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                # JSON.load inherently returns Any as JSON can contain arbitrary data structures.
                # This is a legitimate use of Any - we validate the data when creating model
                # instances in subclasses. The type: ignore is necessary and correct here.
                result = json.load(f)
                return result  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from {path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load file {path}: {e}") from e
