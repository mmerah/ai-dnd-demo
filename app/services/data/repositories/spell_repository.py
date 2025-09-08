"""Repository for managing spell definitions."""

import logging
from typing import Any

from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import IRepository, ISpellRepository
from app.models.magic_school import MagicSchool
from app.models.spell import (
    SpellDamageAtLevel,
    SpellDamageAtSlot,
    SpellDefinition,
    SpellHealingAtSlot,
    SpellSchool,
)
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SpellRepository(BaseRepository[SpellDefinition], ISpellRepository):
    """Repository for loading and managing spell data.

    Follows Single Responsibility Principle: only manages spell data access.
    """

    def __init__(
        self,
        path_resolver: IPathResolver,
        magic_school_repository: IRepository[MagicSchool],
        cache_enabled: bool = True,
    ):
        """Initialize the spell repository.

        Args:
            path_resolver: Service for resolving file paths
            magic_school_repository: Repository for validating magic school references
            cache_enabled: Whether to cache spells in memory
        """
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.spells_file = self.path_resolver.get_shared_data_file("spells")
        self.magic_school_repository = magic_school_repository

    def _initialize(self) -> None:
        """Initialize the repository by loading all spells if caching is enabled."""
        if self.cache_enabled:
            self._load_all_spells()
        self._initialized = True

    def _load_all_spells(self) -> None:
        """Load all spells from the spells.json file into cache."""
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            logger.warning("Spells data file not found or invalid: %s", self.spells_file)
            return

        for spell_data in data.get("spells", []):
            try:
                spell = self._parse_spell_data(spell_data)
                # Key by stable index
                self._cache[spell.index] = spell
            except Exception as e:
                # Log error but continue loading other spells
                logger.warning(f"Failed to load spell {spell_data.get('name', 'unknown')}: {e}")

    def _load_item(self, key: str) -> SpellDefinition | None:
        """Load a single spell by name.

        Args:
            key: Spell name to load

        Returns:
            SpellDefinition or None if not found
        """
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            return None

        # Prefer index match
        for spell_data in data.get("spells", []):
            if spell_data.get("index") == key:
                try:
                    return self._parse_spell_data(spell_data)
                except Exception:
                    return None

        # Fallback: match by name (exact or case-insensitive)
        for spell_data in data.get("spells", []):
            nm = spell_data.get("name", "")
            if nm == key or nm.lower() == key.lower():
                try:
                    return self._parse_spell_data(spell_data)
                except Exception:
                    return None

        return None

    def _get_all_keys(self) -> list[str]:
        """Get all spell names without using cache."""
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            return []

        # Return indexes as keys
        return sorted([spell.get("index", "") for spell in data.get("spells", []) if spell.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        """Check if a spell exists without using cache."""
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            return False

        # Check by index or by name
        for spell_data in data.get("spells", []):
            if spell_data.get("index") == key:
                return True
            nm = spell_data.get("name", "")
            if nm == key or nm.lower() == key.lower():
                return True

        return False

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
        # Any is necessary because spell data from JSON contains mixed types
        """Parse spell data from JSON into SpellDefinition model.

        Args:
            data: Raw spell data from JSON

        Returns:
            Parsed SpellDefinition

        Raises:
            ValueError: If parsing fails
        """
        try:
            # New SRD-aligned structure
            duration = data.get("duration", "")

            # Validate school if repository available (fail-fast)
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
                description=data.get("description", ""),
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
            )
        except Exception as e:
            raise ValueError(f"Failed to parse spell data: {e}") from e

    def get(self, key: str) -> SpellDefinition | None:
        """Get a spell by name, supporting case-insensitive lookup.

        Override base implementation to support case-insensitive matching.

        Args:
            key: Spell name to get

        Returns:
            SpellDefinition or None if not found
        """
        if not self._initialized:
            self._initialize()

        # Try exact match first
        if self.cache_enabled and key in self._cache:
            return self._cache[key]

        # Try case-insensitive match if cached
        if self.cache_enabled:
            for spell_name, spell in self._cache.items():
                if spell_name.lower() == key.lower():
                    return spell

        # Load from file if not cached
        return self._load_item(key)

    def get_by_level(self, level: int) -> list[SpellDefinition]:
        """Get all spells of a specific level.

        Args:
            level: Spell level (0 for cantrips, 1-9 for leveled spells)

        Returns:
            List of spells matching the level
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return [spell for spell in self._cache.values() if spell.level == level]

        # Without cache, load all and filter (coerce/parse level safely)
        all_spells = []
        data = self._load_json_file(self.spells_file)
        if data and isinstance(data, dict):
            for spell_data in data.get("spells", []):
                try:
                    # Coerce level to int if possible; fallback to parsing full model
                    raw_level = spell_data.get("level")
                    lvl = None
                    try:
                        lvl = int(raw_level) if raw_level is not None else None
                    except Exception:
                        lvl = None
                    if lvl is None:
                        spell = self._parse_spell_data(spell_data)
                        if spell.level == level:
                            all_spells.append(spell)
                    elif lvl == level:
                        spell = self._parse_spell_data(spell_data)
                        all_spells.append(spell)
                except Exception:
                    continue

        return all_spells

    def get_by_school(self, school: SpellSchool) -> list[SpellDefinition]:
        """Get all spells of a specific school.

        Args:
            school: School of magic

        Returns:
            List of spells matching the school
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            school_index = school.value.lower()
            return [spell for spell in self._cache.values() if spell.school == school_index]

        # Without cache, load all and filter
        all_spells = []
        data = self._load_json_file(self.spells_file)
        if data and isinstance(data, dict):
            for spell_data in data.get("spells", []):
                try:
                    spell = self._parse_spell_data(spell_data)
                    if spell.school == school.value.lower():
                        all_spells.append(spell)
                except Exception:
                    continue

        return all_spells

    def get_by_class(self, class_name: str) -> list[SpellDefinition]:
        """Get all spells available to a specific class.

        Args:
            class_name: Name of the class (e.g., "Ranger", "Wizard")

        Returns:
            List of spells available to the class
        """
        if not self._initialized:
            self._initialize()

        class_lower = class_name.lower()

        if self.cache_enabled:
            return [spell for spell in self._cache.values() if any(cls.lower() == class_lower for cls in spell.classes)]

        # Without cache, load all and filter
        all_spells = []
        data = self._load_json_file(self.spells_file)
        if data and isinstance(data, dict):
            for spell_data in data.get("spells", []):
                try:
                    classes = spell_data.get("classes", [])
                    if any((cls or "").lower() == class_lower for cls in classes):
                        spell = self._parse_spell_data(spell_data)
                        all_spells.append(spell)
                except Exception:
                    continue

        return all_spells

    def validate_reference(self, key: str) -> bool:
        """Validate by index or name (case-insensitive), even with cache enabled."""
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            if key in self._cache:
                return True
            for k in self._cache:
                if k.lower() == key.lower():
                    return True
            # Fallback to file check (name or index)
            return self._check_key_exists(key)

        return self._check_key_exists(key)
