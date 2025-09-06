"""Repositories for race and subrace catalogs."""

from typing import Any

from app.interfaces.services import IPathResolver
from app.models.attributes import AbilityBonuses
from app.models.race import RaceDefinition, SubraceDefinition
from app.services.data.repositories.base_repository import BaseRepository


class RaceRepository(BaseRepository[RaceDefinition]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("races")

    def _parse_ability_bonuses(self, data: dict[str, int] | None) -> AbilityBonuses | None:
        """Parse ability bonuses from lowercase JSON to uppercase model fields."""
        if not data:
            return None
        return AbilityBonuses(
            STR=data.get("str", 0),
            DEX=data.get("dex", 0),
            CON=data.get("con", 0),
            INT=data.get("int", 0),
            WIS=data.get("wis", 0),
            CHA=data.get("cha", 0),
        )

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return
        for item in data.get("races", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> RaceDefinition | None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return None
        for item in data.get("races", []):
            if item.get("index") == key or (item.get("name") or "").lower() == key.lower():
                try:
                    return self._parse(item)
                except Exception:
                    return None
        return None

    def _get_all_keys(self) -> list[str]:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("races", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return False
        for item in data.get("races", []):
            if item.get("index") == key:
                return True
            if (item.get("name") or "").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> RaceDefinition:
        return RaceDefinition(
            index=data["index"],
            name=data["name"],
            speed=int(data.get("speed", 30)),
            size=data.get("size", "Medium"),
            languages=data.get("languages", []),
            description=data.get("description"),
            traits=data.get("traits"),
            subraces=data.get("subraces"),
            ability_bonuses=self._parse_ability_bonuses(data.get("ability_bonuses")),
            weapon_proficiencies=data.get("weapon_proficiencies"),
            tool_proficiencies=data.get("tool_proficiencies"),
            language_options=data.get("language_options"),
        )


class SubraceRepository(BaseRepository[SubraceDefinition]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("subraces")

    def _parse_ability_bonuses(self, data: dict[str, int] | None) -> AbilityBonuses | None:
        """Parse ability bonuses from lowercase JSON to uppercase model fields."""
        if not data:
            return None
        return AbilityBonuses(
            STR=data.get("str", 0),
            DEX=data.get("dex", 0),
            CON=data.get("con", 0),
            INT=data.get("int", 0),
            WIS=data.get("wis", 0),
            CHA=data.get("cha", 0),
        )

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return
        for item in data.get("subraces", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> SubraceDefinition | None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return None
        for item in data.get("subraces", []):
            if item.get("index") == key or (item.get("name") or "").lower() == key.lower():
                try:
                    return self._parse(item)
                except Exception:
                    return None
        return None

    def _get_all_keys(self) -> list[str]:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("subraces", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return False
        for item in data.get("subraces", []):
            if item.get("index") == key:
                return True
            if (item.get("name") or "").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> SubraceDefinition:
        return SubraceDefinition(
            index=data["index"],
            name=data["name"],
            parent_race=data["parent_race"],
            description=data.get("description"),
            traits=data.get("traits"),
            ability_bonuses=self._parse_ability_bonuses(data.get("ability_bonuses")),
            weapon_proficiencies=data.get("weapon_proficiencies"),
            tool_proficiencies=data.get("tool_proficiencies"),
        )
