"""Repository for managing spell definitions."""

import logging
from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.interfaces.services.data import IRepository
from app.models.magic_school import MagicSchool
from app.models.spell import (
    SpellDamageAtLevel,
    SpellDamageAtSlot,
    SpellDefinition,
    SpellHealingAtSlot,
)
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SpellRepository(BaseRepository[SpellDefinition]):
    """Repository for loading and managing spell data."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        magic_school_repository: IRepository[MagicSchool],
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        """Initialize the spell repository.

        Args:
            path_resolver: Service for resolving file paths
            magic_school_repository: Repository for validating magic school references
            cache_enabled: Whether to cache spells in memory
            content_pack_registry: Registry for managing content packs
            content_packs: List of content pack IDs to load from
        """
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver
        self.magic_school_repository = magic_school_repository

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "spells"

    def _parse_item(self, data: dict[str, Any]) -> SpellDefinition:
        """Parse raw item data into model instance."""
        return self._parse_spell_data(data)

    def _parse_damage_at_slot(self, data: dict[int | str, str] | None) -> SpellDamageAtSlot | None:
        """Parse damage at slot level from JSON to model."""
        if not data:
            return None
        return SpellDamageAtSlot(
            slot_1=data.get(1) or data.get("1"),
            slot_2=data.get(2) or data.get("2"),
            slot_3=data.get(3) or data.get("3"),
            slot_4=data.get(4) or data.get("4"),
            slot_5=data.get(5) or data.get("5"),
            slot_6=data.get(6) or data.get("6"),
            slot_7=data.get(7) or data.get("7"),
            slot_8=data.get(8) or data.get("8"),
            slot_9=data.get(9) or data.get("9"),
        )

    def _parse_healing_at_slot(self, data: dict[int | str, str | int] | None) -> SpellHealingAtSlot | None:
        """Parse healing at slot level from JSON to model."""
        if not data:
            return None
        return SpellHealingAtSlot(
            slot_1=data.get(1) or data.get("1"),
            slot_2=data.get(2) or data.get("2"),
            slot_3=data.get(3) or data.get("3"),
            slot_4=data.get(4) or data.get("4"),
            slot_5=data.get(5) or data.get("5"),
            slot_6=data.get(6) or data.get("6"),
            slot_7=data.get(7) or data.get("7"),
            slot_8=data.get(8) or data.get("8"),
            slot_9=data.get(9) or data.get("9"),
        )

    def _parse_damage_at_level(self, data: dict[int | str, str] | None) -> SpellDamageAtLevel | None:
        """Parse damage at character level from JSON to model."""
        if not data:
            return None
        return SpellDamageAtLevel(
            level_1=data.get(1) or data.get("1"),
            level_5=data.get(5) or data.get("5"),
            level_11=data.get(11) or data.get("11"),
            level_17=data.get(17) or data.get("17"),
        )

    def _parse_spell_data(self, data: dict[str, Any]) -> SpellDefinition:
        """Parse spell data from JSON into SpellDefinition model."""
        try:
            # New SRD-aligned structure
            duration = data.get("duration", "")

            # Validate school if repository available
            school = str(data.get("school", "")).lower()
            if school and not self.magic_school_repository.validate_reference(school):
                raise ValueError(f"Unknown magic school: {school}")

            return SpellDefinition(
                index=data["index"],
                name=data["name"],
                level=int(data["level"]),
                school=school,
                casting_time=data.get("casting_time", ""),
                range=data.get("range", ""),
                duration=duration,
                description=data["description"],
                higher_levels=data.get("higher_levels"),
                components_list=data.get("components_list", []),
                material=data.get("material"),
                ritual=bool(data.get("ritual", False)),
                concentration=bool(data.get("concentration", False)),
                classes=data.get("classes", []),
                subclasses=data.get("subclasses", []),
                area_of_effect=data.get("area_of_effect"),
                attack_type=data.get("attack_type"),
                dc=data.get("dc"),
                damage_at_slot_level=self._parse_damage_at_slot(data.get("damage_at_slot_level")),
                heal_at_slot_level=self._parse_healing_at_slot(data.get("heal_at_slot_level")),
                damage_at_character_level=self._parse_damage_at_level(data.get("damage_at_character_level")),
                content_pack=data["content_pack"],
            )
        except Exception as e:
            raise ValueError(f"Failed to parse spell data: {e}") from e
