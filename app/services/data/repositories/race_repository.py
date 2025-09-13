"""Repositories for race and subrace catalogs."""

from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.models.attributes import AbilityBonuses
from app.models.race import RaceDefinition, SubraceDefinition
from app.services.data.repositories.base_repository import BaseRepository


class RaceRepository(BaseRepository[RaceDefinition]):
    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

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

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "races"

    def _parse_item(self, data: dict[str, Any]) -> RaceDefinition:
        """Parse raw item data into model instance."""
        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> RaceDefinition:
        return RaceDefinition(
            index=data["index"],
            name=data["name"],
            speed=int(data.get("speed", 30)),
            size=data.get("size", "Medium"),
            languages=data.get("languages", []),
            description=data["description"],
            traits=data.get("traits"),
            subraces=data.get("subraces"),
            ability_bonuses=self._parse_ability_bonuses(data.get("ability_bonuses")),
            weapon_proficiencies=data.get("weapon_proficiencies"),
            tool_proficiencies=data.get("tool_proficiencies"),
            language_options=data.get("language_options"),
            content_pack=data["content_pack"],
        )


class SubraceRepository(BaseRepository[SubraceDefinition]):
    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

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

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "subraces"

    def _parse_item(self, data: dict[str, Any]) -> SubraceDefinition:
        """Parse raw item data into model instance."""
        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> SubraceDefinition:
        return SubraceDefinition(
            index=data["index"],
            name=data["name"],
            parent_race=data["parent_race"],
            description=data["description"],
            traits=data.get("traits"),
            ability_bonuses=self._parse_ability_bonuses(data.get("ability_bonuses")),
            weapon_proficiencies=data.get("weapon_proficiencies"),
            tool_proficiencies=data.get("tool_proficiencies"),
            content_pack=data["content_pack"],
        )
