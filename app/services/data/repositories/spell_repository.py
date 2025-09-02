"""Repository for managing spell definitions."""

import logging
from typing import Any

from app.interfaces.services import IPathResolver, ISpellRepository
from app.models.spell import SpellDefinition, SpellSchool
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SpellRepository(BaseRepository[SpellDefinition], ISpellRepository):
    """Repository for loading and managing spell data.

    Follows Single Responsibility Principle: only manages spell data access.
    """

    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        """Initialize the spell repository.

        Args:
            path_resolver: Service for resolving file paths
            cache_enabled: Whether to cache spells in memory
        """
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.spells_file = self.path_resolver.get_shared_data_file("spells")

    def _initialize(self) -> None:
        """Initialize the repository by loading all spells if caching is enabled."""
        if self.cache_enabled:
            self._load_all_spells()
        self._initialized = True

    def _load_all_spells(self) -> None:
        """Load all spells from the spells.json file into cache."""
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            raise FileNotFoundError(f"Spells data file not found: {self.spells_file}")

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
            return SpellDefinition(
                index=data["index"],
                name=data["name"],
                level=int(data["level"]),
                school=str(data.get("school", "")).lower(),
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
                damage_at_slot_level=data.get("damage_at_slot_level"),
                heal_at_slot_level=data.get("heal_at_slot_level"),
                damage_at_character_level=data.get("damage_at_character_level"),
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

        # Without cache, load all and filter
        all_spells = []
        data = self._load_json_file(self.spells_file)
        if data and isinstance(data, dict):
            for spell_data in data.get("spells", []):
                try:
                    if spell_data.get("level") == level:
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
