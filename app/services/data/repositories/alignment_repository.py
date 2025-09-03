"""Repository for managing alignment catalog."""

from typing import Any

from app.interfaces.services import IPathResolver
from app.models.alignment import Alignment
from app.services.data.repositories.base_repository import BaseRepository


class AlignmentRepository(BaseRepository[Alignment]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("alignments")

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not data or not isinstance(data, dict):
            return
        for item in data.get("alignments", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> Alignment | None:
        data = self._load_json_file(self.file)
        if not data or not isinstance(data, dict):
            return None
        for item in data.get("alignments", []):
            idx = item.get("index")
            name = item.get("name")
            if idx == key or (isinstance(name, str) and name.lower() == key.lower()):
                try:
                    return self._parse(item)
                except Exception:
                    return None
        return None

    def _get_all_keys(self) -> list[str]:
        data = self._load_json_file(self.file)
        if not data or not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("alignments", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not data or not isinstance(data, dict):
            return False
        for item in data.get("alignments", []):
            if item.get("index") == key:
                return True
            if isinstance(item.get("name"), str) and item.get("name").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> Alignment:
        return Alignment(
            index=data["index"],
            name=data["name"],
            description=data.get("description") or data.get("desc", ""),
        )
