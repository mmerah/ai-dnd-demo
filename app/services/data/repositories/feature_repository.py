"""Repository for features catalog."""

from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.models.feature import FeatureDefinition, FeatureGrantedBy
from app.services.data.repositories.base_repository import BaseRepository


class FeatureRepository(BaseRepository[FeatureDefinition]):
    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "features"

    def _parse_item(self, data: dict[str, Any]) -> FeatureDefinition:
        """Parse raw item data into model instance."""
        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> FeatureDefinition:
        granted_by_data: dict[str, Any] = data["granted_by"]
        granted_by = FeatureGrantedBy(
            class_index=granted_by_data["class"],
            subclass_index=granted_by_data.get("subclass"),
        )

        return FeatureDefinition(
            index=data["index"],
            name=data["name"],
            description=data["description"],
            class_index=data["class_index"],
            subclass_index=data.get("subclass_index"),
            level=data["level"],
            granted_by=granted_by,
            content_pack=data["content_pack"],
        )
