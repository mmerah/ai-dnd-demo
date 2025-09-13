"""Base repository pattern for data access."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.common import IContentPackRegistry
from app.interfaces.services.data import IRepository

logger = logging.getLogger(__name__)


# Repository items must be Pydantic models
T = TypeVar("T", bound=BaseModel)


class BaseRepository(IRepository[T], ABC, Generic[T]):
    """Abstract base class for repositories.

    Provides common functionality for caching, loading, and error handling.
    Supports loading from multiple content packs with conflict resolution.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        """Initialize the base repository.

        Args:
            cache_enabled: Whether to cache loaded data in memory
            content_pack_registry: Registry for managing content packs
            content_packs: List of content pack IDs to load from (defaults to ['srd'])
        """
        if content_pack_registry is None or content_packs is None:
            raise ValueError("ContentPackRegistry and content_packs are required for repositories")
        self.cache_enabled = cache_enabled
        self.content_pack_registry = content_pack_registry
        self.content_packs = content_packs
        self._cache: dict[str, T] = {}
        self._pack_cache: dict[str, dict[str, T]] = {}  # Pack-specific caches
        self._item_pack_map: dict[str, str] = {}  # Track which pack each item came from
        self._initialized = False

    def get(self, key: str) -> T:
        if not self._initialized:
            self._initialize()

        if self.cache_enabled and key in self._cache:
            return self._cache[key]

        item = self._load_item(key)
        if item:
            if self.cache_enabled:
                self._cache[key] = item
            return item

        raise RepositoryNotFoundError(f"Item with key '{key}' not found")

    def list_keys(self) -> list[str]:
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return sorted(self._cache.keys())

        return self._get_all_keys()

    def get_name(self, key: str) -> str:
        """Get the display name for a given key."""
        item = self.get(key)
        # Use getattr since T is generic and mypy can't verify .name exists
        name = getattr(item, "name", None)
        if name is None:
            raise ValueError(f"Item {key} has no 'name' attribute")
        return str(name)

    def validate_reference(self, key: str) -> bool:
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return key in self._cache

        return self._check_key_exists(key)

    def _get_ordered_packs(self) -> list[str]:
        """Get content packs in correct loading order.

        Returns:
            Ordered list of pack IDs with dependencies resolved
        """
        try:
            return self.content_pack_registry.get_pack_order(self.content_packs)
        except Exception as e:
            logger.warning(f"Failed to resolve pack order: {e}. Using provided order.")
            return self.content_packs

    def _merge_pack_data(self, data_by_pack: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        """Merge data from multiple packs with conflict resolution.

        Later packs override earlier ones for items with the same key.

        Args:
            data_by_pack: Dictionary mapping pack IDs to their data items

        Returns:
            Merged list of data items
        """
        merged: dict[str, dict[str, Any]] = {}

        # Process packs in order, allowing later packs to override
        for pack_id in self._get_ordered_packs():
            if pack_id not in data_by_pack:
                continue

            for item in data_by_pack[pack_id]:
                # Get the key for this item (index or name)
                key = self._get_item_key(item)
                if key:
                    merged[key] = item
                    # Track which pack this item came from
                    if self.cache_enabled:
                        self._item_pack_map[key] = pack_id

        return list(merged.values())

    def get_item_pack_id(self, key: str) -> str | None:
        """Return the pack id that provided this key (if known).

        Only populated when cache is enabled and data was loaded via content packs.
        """
        if not self._initialized:
            self._initialize()
        return self._item_pack_map.get(key)

    def filter(self, *predicates: Callable[[T], bool]) -> list[T]:
        """Filter repository items using one or more predicate functions.

        All predicates must return True for an item to be included (AND logic).
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            # Filter from cache
            results = []
            for item in self._cache.values():
                if all(pred(item) for pred in predicates):
                    results.append(item)
            return results

        # Without cache, load all items and filter
        # This is less efficient but maintains the same interface
        all_items = self._load_all_items_uncached()
        results = []
        for item in all_items:
            if all(pred(item) for pred in predicates):
                results.append(item)
        return results

    def _load_all_items_uncached(self) -> list[T]:
        """Load all items without using cache.

        This is used by filter when cache is disabled.
        Subclasses should override if they have a more efficient way.
        """
        items = []
        for key in self._get_all_keys():
            try:
                item = self._load_item(key)
                if item:
                    items.append(item)
            except Exception:
                continue
        return items

    def _load_items_from_pack(self, pack_id: str) -> list[dict[str, Any]]:
        """Load items from a single content pack.

        Handles both regular content packs and scenario-specific packs.

        Args:
            pack_id: The pack ID to load from

        Returns:
            List of item data dictionaries
        """
        # Handle scenario packs (directory of individual files)
        if pack_id.startswith("scenario:"):
            return self._load_scenario_items(pack_id)

        # Regular content pack with consolidated JSON
        return self._load_regular_pack_items(pack_id)

    def _load_scenario_items(self, pack_id: str) -> list[dict[str, Any]]:
        """Load items from a scenario pack (individual files).

        Args:
            pack_id: The scenario pack ID

        Returns:
            List of item data dictionaries
        """
        data_type = self._get_data_type()
        items_path = self.content_pack_registry.get_pack_data_path(pack_id, data_type)
        if not items_path or not items_path.is_dir():
            return []

        pack_items = []
        for item_file in items_path.glob("*.json"):
            item_data = self._load_json_file(item_file)
            if item_data and isinstance(item_data, dict):
                # Handle wrapped scenario data (e.g., ScenarioMonster with 'monster' field)
                if data_type == "monsters" and "monster" in item_data:
                    inner_data = item_data["monster"]
                    inner_data["content_pack"] = pack_id
                    pack_items.append(inner_data)
                else:
                    # Regular item data
                    item_data["content_pack"] = pack_id
                    pack_items.append(item_data)
        return pack_items

    def _load_regular_pack_items(self, pack_id: str) -> list[dict[str, Any]]:
        """Load items from a regular content pack (consolidated JSON).

        Args:
            pack_id: The pack ID

        Returns:
            List of item data dictionaries
        """
        data_type = self._get_data_type()
        pack_items = []

        # Load regular items
        items_path = self.content_pack_registry.get_pack_data_path(pack_id, data_type)
        if items_path:
            data = self._load_json_file(items_path)
            if data and isinstance(data, dict):
                pack_items.extend(data.get(data_type, []))

        # Special case: items repository also loads magic_items
        if data_type == "items":
            magic_items_path = self.content_pack_registry.get_pack_data_path(pack_id, "magic_items")
            if magic_items_path:
                data = self._load_json_file(magic_items_path)
                if data and isinstance(data, dict):
                    pack_items.extend(data.get("items", []))

        return pack_items

    @abstractmethod
    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data.

        Args:
            item_data: Raw item data from JSON

        Returns:
            Unique key for the item, or None if invalid
        """
        pass

    @abstractmethod
    def _get_data_type(self) -> str:
        """Get the data type name for this repository.

        Used to determine file names and JSON keys.
        Examples: 'items', 'spells', 'monsters'

        Returns:
            The data type name
        """
        pass

    @abstractmethod
    def _parse_item(self, data: dict[str, Any]) -> T:
        """Parse raw item data into model instance.

        Args:
            data: Raw item data from JSON

        Returns:
            Parsed model instance

        Raises:
            ValueError: If parsing fails
        """
        pass

    def _initialize(self) -> None:
        """Initialize the repository, loading data if cache is enabled."""
        if self.cache_enabled:
            self._load_all_items()
        self._initialized = True

    def _load_all_items(self) -> None:
        """Load all items from content packs into cache."""
        data_by_pack: dict[str, list[dict[str, Any]]] = {}

        for pack_id in self._get_ordered_packs():
            pack_items = self._load_items_from_pack(pack_id)
            if pack_items:
                data_by_pack[pack_id] = pack_items

        # Merge and load items
        merged_items = self._merge_pack_data(data_by_pack)
        for item_data in merged_items:
            try:
                item = self._parse_item(item_data)
                key = self._get_item_key(item_data)
                if key:
                    self._cache[key] = item
            except Exception as e:
                logger.warning(f"Failed to load {self._get_data_type()} item: {e}")

    def _load_item(self, key: str) -> T | None:
        """Load a single item by key.

        Args:
            key: The key to load

        Returns:
            The loaded item or None if not found
        """
        # Search through content packs in order
        for pack_id in self._get_ordered_packs():
            pack_items = self._load_items_from_pack(pack_id)
            for item_data in pack_items:
                if str(item_data.get("index", "")) == key:
                    try:
                        return self._parse_item(item_data)
                    except Exception:
                        continue
        return None

    def _get_all_keys(self) -> list[str]:
        """Get all available keys without using cache.

        Returns:
            List of all keys
        """
        keys: set[str] = set()

        # Get keys from all content packs
        for pack_id in self._get_ordered_packs():
            pack_items = self._load_items_from_pack(pack_id)
            for item in pack_items:
                key = item.get("index", "")
                if key:
                    keys.add(str(key))

        return sorted(keys)

    def _check_key_exists(self, key: str) -> bool:
        """Check if a key exists without using cache.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        # Search through content packs
        for pack_id in self._get_ordered_packs():
            pack_items = self._load_items_from_pack(pack_id)
            for item in pack_items:
                if str(item.get("index", "")) == key:
                    return True
        return False

    def _load_json_file(self, path: Path) -> dict[str, Any] | list[Any] | None:
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
                result = json.load(f)
                return result  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON from {path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load file {path}: {e}") from e
