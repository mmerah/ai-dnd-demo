"""Repository for managing item definitions."""

from typing import Any

from app.interfaces.services import IItemRepository, IPathResolver
from app.models.item import ItemDefinition, ItemRarity, ItemSubtype, ItemType
from app.services.data.repositories.base_repository import BaseRepository


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

    def _initialize(self) -> None:
        """Initialize the repository by loading all items if caching is enabled."""
        if self.cache_enabled:
            self._load_all_items()
        self._initialized = True

    def _load_all_items(self) -> None:
        """Load all items from the items.json file into cache."""
        data = self._load_json_file(self.items_file)
        if not data or not isinstance(data, dict):
            raise FileNotFoundError(f"Items data file not found: {self.items_file}")

        for item_data in data.get("items", []):
            try:
                item = self._parse_item_data(item_data)
                self._cache[item.name] = item
            except Exception as e:
                # Log error but continue loading other items
                print(f"Warning: Failed to load item {item_data.get('name', 'unknown')}: {e}")

    def _load_item(self, key: str) -> ItemDefinition | None:
        """Load a single item by name.

        Args:
            key: Item name to load

        Returns:
            ItemDefinition or None if not found
        """
        data = self._load_json_file(self.items_file)
        if not data or not isinstance(data, dict):
            return None

        for item_data in data.get("items", []):
            if item_data.get("name") == key:
                try:
                    return self._parse_item_data(item_data)
                except Exception:
                    return None

        return None

    def _get_all_keys(self) -> list[str]:
        """Get all item names without using cache."""
        data = self._load_json_file(self.items_file)
        if not data or not isinstance(data, dict):
            return []

        return sorted([item.get("name", "") for item in data.get("items", []) if item.get("name")])

    def _check_key_exists(self, key: str) -> bool:
        """Check if an item exists without using cache."""
        data = self._load_json_file(self.items_file)
        if not data or not isinstance(data, dict):
            return False

        return any(item.get("name") == key for item in data.get("items", []))

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
                capacity=data.get("capacity"),
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
