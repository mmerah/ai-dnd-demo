"""Repository for managing item definitions."""

import logging
from typing import Any

from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import IItemRepository
from app.models.item import ItemDefinition, ItemRarity, ItemSubtype, ItemType
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ItemRepository(BaseRepository[ItemDefinition], IItemRepository):
    """Repository for loading and managing item data.

    Follows Single Responsibility Principle: only manages item data access.
    """

    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        """Initialize the item repository.

        Args:
            path_resolver: Service for resolving file paths
            cache_enabled: Whether to cache items in memory
        """
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.items_file = self.path_resolver.get_shared_data_file("items")
        self.magic_items_file = self.path_resolver.get_shared_data_file("magic_items")

    def _initialize(self) -> None:
        """Initialize the repository by loading all items if caching is enabled."""
        if self.cache_enabled:
            self._load_all_items()
        self._initialized = True

    def _load_all_items(self) -> None:
        """Load all items from the items.json file into cache."""
        sources = [self.items_file, self.magic_items_file]
        any_found = False
        for src in sources:
            data = self._load_json_file(src)
            if data and isinstance(data, dict):
                any_found = True
                for item_data in data.get("items", []):
                    try:
                        item = self._parse_item_data(item_data)
                        key = item_data.get("index") or item.name
                        self._cache[str(key)] = item
                    except Exception as e:
                        logger.warning(f"Failed to load item {item_data.get('name', 'unknown')} from {src}: {e}")
        if not any_found:
            logger.warning("Items data files not found or invalid: %s", sources)

    def _load_item(self, key: str) -> ItemDefinition | None:
        """Load a single item by name.

        Args:
            key: Item name to load

        Returns:
            ItemDefinition or None if not found
        """
        for src in [self.items_file, self.magic_items_file]:
            data = self._load_json_file(src)
            if not data or not isinstance(data, dict):
                continue
            for item_data in data.get("items", []):
                idx = str(item_data.get("index", ""))
                nm = item_data.get("name", "")
                if idx == key or (idx and idx.lower() == key.lower()) or nm == key or nm.lower() == key.lower():
                    try:
                        return self._parse_item_data(item_data)
                    except Exception:
                        return None

        return None

    def _get_all_keys(self) -> list[str]:
        """Get all item names without using cache."""
        names: set[str] = set()
        for src in [self.items_file, self.magic_items_file]:
            data = self._load_json_file(src)
            if not data or not isinstance(data, dict):
                continue
            for item in data.get("items", []):
                key = item.get("index") or item.get("name", "")
                if key:
                    names.add(str(key))
        return sorted(names)

    def _check_key_exists(self, key: str) -> bool:
        """Check if an item exists without using cache."""
        for src in [self.items_file, self.magic_items_file]:
            data = self._load_json_file(src)
            if not data or not isinstance(data, dict):
                continue
            for item in data.get("items", []):
                idx = str(item.get("index", ""))
                nm = item.get("name", "")
                if idx == key or (idx and idx.lower() == key.lower()) or nm == key or nm.lower() == key.lower():
                    return True
        return False

    def _parse_item_data(self, data: dict[str, Any]) -> ItemDefinition:
        # Any is necessary because item data from JSON contains mixed types
        """Parse item data from JSON into ItemDefinition model.

        Args:
            data: Raw item data from JSON

        Returns:
            Parsed ItemDefinition

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Map string values to enums
            item_type = ItemType(data["type"])
            rarity = ItemRarity(data["rarity"])
            subtype = ItemSubtype(data["subtype"]) if data.get("subtype") else None

            return ItemDefinition(
                name=data["name"],
                type=item_type,
                rarity=rarity,
                weight=data.get("weight", 0.0),
                value=data.get("value", 0),
                description=data.get("description", ""),
                subtype=subtype,
                damage=data.get("damage"),
                damage_type=data.get("damage_type"),
                properties=data.get("properties", []),
                armor_class=data.get("armor_class"),
                dex_bonus=data.get("dex_bonus"),
                contents=data.get("contents", []),
                quantity_available=data.get("quantity_available"),
            )
        except Exception as e:
            raise ValueError(f"Failed to parse item data: {e}") from e

    def get_by_type(self, item_type: ItemType) -> list[ItemDefinition]:
        """Get all items of a specific type.

        Args:
            item_type: Type of items to retrieve

        Returns:
            List of items matching the type
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return [item for item in self._cache.values() if item.type == item_type]

        # Without cache, load all and filter
        all_items = []
        data = self._load_json_file(self.items_file)
        if data and isinstance(data, dict):
            for item_data in data.get("items", []):
                try:
                    item = self._parse_item_data(item_data)
                    if item.type == item_type:
                        all_items.append(item)
                except Exception:
                    continue

        return all_items

    def get_by_rarity(self, rarity: ItemRarity) -> list[ItemDefinition]:
        """Get all items of a specific rarity.

        Args:
            rarity: Rarity level to filter by

        Returns:
            List of items matching the rarity
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return [item for item in self._cache.values() if item.rarity == rarity]

        # Without cache, load all and filter
        all_items = []
        data = self._load_json_file(self.items_file)
        if data and isinstance(data, dict):
            for item_data in data.get("items", []):
                try:
                    item = self._parse_item_data(item_data)
                    if item.rarity == rarity:
                        all_items.append(item)
                except Exception:
                    continue

        return all_items

    def validate_reference(self, key: str) -> bool:
        """Validate item by index or name (case-insensitive), even with cache enabled."""
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            if key in self._cache:
                return True
            lower = key.lower()
            for k, v in self._cache.items():
                if k.lower() == lower or v.name.lower() == lower:
                    return True
            return self._check_key_exists(key)

        return self._check_key_exists(key)
