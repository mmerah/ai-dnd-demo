"""Repository for weapon properties catalog."""

from typing import Any

from app.interfaces.services import IPathResolver
from app.models.weapon_property import WeaponProperty
from app.services.data.repositories.base_repository import BaseRepository


class WeaponPropertyRepository(BaseRepository[WeaponProperty]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("weapon_properties")

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return
        for item in data.get("weapon_properties", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> WeaponProperty | None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return None
        for item in data.get("weapon_properties", []):
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
        if not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("weapon_properties", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return False
        for item in data.get("weapon_properties", []):
            if item.get("index") == key:
                return True
            if isinstance(item.get("name"), str) and item.get("name").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> WeaponProperty:
        return WeaponProperty(
            index=data["index"],
            name=data["name"],
            description=data.get("description")
            or ("\n\n".join(data.get("desc", [])) if isinstance(data.get("desc"), list) else data.get("desc", "")),
        )
