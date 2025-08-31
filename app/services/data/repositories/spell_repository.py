"""Repository for managing spell definitions."""

from typing import Any

from app.interfaces.services import IPathResolver, ISpellRepository
from app.models.spell import SpellDefinition, SpellSchool
from app.services.data.repositories.base_repository import BaseRepository


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
                self._cache[spell.name] = spell
            except Exception as e:
                # Log error but continue loading other spells
                print(f"Warning: Failed to load spell {spell_data.get('name', 'unknown')}: {e}")

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

        # Try exact match first
        for spell_data in data.get("spells", []):
            if spell_data.get("name") == key:
                try:
                    return self._parse_spell_data(spell_data)
                except Exception:
                    return None

        # Try case-insensitive match
        for spell_data in data.get("spells", []):
            if spell_data.get("name", "").lower() == key.lower():
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

        return sorted([spell.get("name", "") for spell in data.get("spells", []) if spell.get("name")])

    def _check_key_exists(self, key: str) -> bool:
        """Check if a spell exists without using cache."""
        data = self._load_json_file(self.spells_file)
        if not data or not isinstance(data, dict):
            return False

        # Check both exact and case-insensitive match
        for spell_data in data.get("spells", []):
            spell_name = spell_data.get("name", "")
            if spell_name == key or spell_name.lower() == key.lower():
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
            # Map string school to enum
            school = SpellSchool(data["school"])

            # Check if spell requires concentration
            duration = data.get("duration", "")
            concentration = "concentration" in duration.lower()

            return SpellDefinition(
                name=data["name"],
                level=data["level"],
                school=school,
                casting_time=data["casting_time"],
                range=data["range"],
                components=data["components"],
                duration=duration,
                description=data["description"],
                higher_levels=data.get("higher_levels"),
                classes=data.get("classes", []),
                ritual=data.get("ritual", False),
                concentration=concentration,
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
            return [spell for spell in self._cache.values() if spell.school == school]

        # Without cache, load all and filter
        all_spells = []
        data = self._load_json_file(self.spells_file)
        if data and isinstance(data, dict):
            for spell_data in data.get("spells", []):
                try:
                    spell = self._parse_spell_data(spell_data)
                    if spell.school == school:
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
                    if any(cls.lower() == class_lower for cls in classes):
                        spell = self._parse_spell_data(spell_data)
                        all_spells.append(spell)
                except Exception:
                    continue

        return all_spells
