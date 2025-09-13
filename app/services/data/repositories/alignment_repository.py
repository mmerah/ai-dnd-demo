"""Repository for managing alignment catalog."""

from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.models.alignment import Alignment
from app.services.data.repositories.base_repository import BaseRepository


class AlignmentRepository(BaseRepository[Alignment]):
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
        return "alignments"

    def _parse_item(self, data: dict[str, Any]) -> Alignment:
        """Parse raw item data into model instance."""
        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> Alignment:
        return Alignment(
            index=data["index"],
            name=data["name"],
            description=data["description"],
            content_pack=data["content_pack"],
        )
