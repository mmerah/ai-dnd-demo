"""Repository for managing item definitions."""

import logging
from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.models.item import ItemDefinition, ItemRarity, ItemSubtype, ItemType
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ItemRepository(BaseRepository[ItemDefinition]):
    """Repository for loading and managing item data."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        """Initialize the item repository.

        Args:
            path_resolver: Service for resolving file paths
            cache_enabled: Whether to cache items in memory
            content_pack_registry: Registry for managing content packs
            content_packs: List of content pack IDs to load from
        """
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data (index required)."""
        if "index" not in item_data or item_data.get("index") in (None, ""):
            return None
        return str(item_data["index"])

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "items"

    def _parse_item(self, data: dict[str, Any]) -> ItemDefinition:
        """Parse raw item data into model instance."""
        return self._parse_item_data(data)

    def _parse_item_data(self, data: dict[str, Any]) -> ItemDefinition:
        """Parse item data from JSON into ItemDefinition model."""
        try:
            return ItemDefinition(
                index=data["index"],
                name=data["name"],
                type=ItemType(data["type"]),
                rarity=ItemRarity(data["rarity"]),
                weight=float(data.get("weight") or 0.0),
                value=float(data.get("value") or 0.0),
                description=data.get("description") or "",
                subtype=ItemSubtype(data["subtype"]) if data.get("subtype") else None,
                damage=data.get("damage") or "",
                damage_type=data.get("damage_type") or "",
                properties=list(data.get("properties") or []),
                armor_class=int(data.get("armor_class") or 0),
                dex_bonus=bool(data.get("dex_bonus") or False),
                contents=list(data.get("contents") or []),
                quantity_available=int(data.get("quantity_available") or -1),
                content_pack=data["content_pack"],
            )
        except Exception as e:
            raise ValueError(f"Failed to parse item data: {e}") from e
