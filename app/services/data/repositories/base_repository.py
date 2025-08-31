"""Base repository pattern for data access."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.interfaces.services import IRepository

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

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()

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
                # json.load returns Any, which is what we need for arbitrary JSON data
                result = json.load(f)
                return result  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from {path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load file {path}: {e}") from e

    def _save_json_file(self, path: Path, data: dict[str, Any] | list[Any]) -> None:
        # Any is necessary here because we're saving arbitrary JSON-serializable data
        """Helper method to save JSON to a file.

        Args:
            path: Path to save the JSON file
            data: Data to save

        Raises:
            RuntimeError: If saving fails
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save file {path}: {e}") from e
