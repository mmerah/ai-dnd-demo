"""Repository for managing monster definitions."""

import logging
from typing import Any

from app.interfaces.services import IMonsterRepository, IPathResolver
from app.models.npc import NPCSheet
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MonsterRepository(BaseRepository[NPCSheet], IMonsterRepository):
    """Repository for loading and managing monster data.

    Follows Single Responsibility Principle: only manages monster data access.
    """

    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        """Initialize the monster repository.

        Args:
            path_resolver: Service for resolving file paths
            cache_enabled: Whether to cache monsters in memory
        """
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.monsters_file = self.path_resolver.get_shared_data_file("monsters")

    def _initialize(self) -> None:
        """Initialize the repository by loading all monsters if caching is enabled."""
        if self.cache_enabled:
            self._load_all_monsters()
        self._initialized = True

    def _load_all_monsters(self) -> None:
        """Load all monsters from the monsters.json file into cache."""
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            raise FileNotFoundError(f"Monsters data file not found: {self.monsters_file}")

        for monster_data in data.get("monsters", []):
            try:
                monster = self._parse_monster_data(monster_data)
                self._cache[monster.name] = monster
            except Exception as e:
                # Log error but continue loading other monsters
                logger.warning(f"Failed to load monster {monster_data.get('name', 'unknown')}: {e}")

    def _load_item(self, key: str) -> NPCSheet | None:
        """Load a single monster by name.

        Args:
            key: Monster name to load

        Returns:
            NPCSheet or None if not found
        """
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            return None

        for monster_data in data.get("monsters", []):
            if monster_data.get("name") == key:
                try:
                    return self._parse_monster_data(monster_data)
                except Exception:
                    return None

        return None

    def _get_all_keys(self) -> list[str]:
        """Get all monster names without using cache."""
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            return []

        return sorted([monster.get("name", "") for monster in data.get("monsters", []) if monster.get("name")])

    def _check_key_exists(self, key: str) -> bool:
        """Check if a monster exists without using cache."""
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            return False

        return any(monster.get("name") == key for monster in data.get("monsters", []))

    def _parse_monster_data(self, data: dict[str, Any]) -> NPCSheet:
        # Any is necessary because monster data from JSON contains mixed types
        """Parse monster data from JSON into NPCSheet model.

        Args:
            data: Raw monster data from JSON

        Returns:
            Parsed NPCSheet

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Convert hit_points to proper format if needed
            if isinstance(data.get("hit_points"), int):
                data["hit_points"] = {
                    "current": data["hit_points"],
                    "maximum": data["hit_points"],
                    "temporary": 0,
                }

            # Create NPCSheet from data
            return NPCSheet(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse monster data: {e}") from e

    def get(self, key: str) -> NPCSheet | None:
        """Get a monster by name, returning a deep copy.

        Override base implementation to return deep copies to avoid
        modifying the cached version.

        Args:
            key: Monster name to get

        Returns:
            Deep copy of NPCSheet or None if not found
        """
        monster = super().get(key)
        if monster:
            # Return a deep copy to avoid modifying the cached version
            return monster.model_copy(deep=True)
        return None

    def get_by_challenge_rating(self, min_cr: float, max_cr: float) -> list[NPCSheet]:
        """Get all monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating (inclusive)
            max_cr: Maximum challenge rating (inclusive)

        Returns:
            List of monsters within the CR range
        """
        if not self._initialized:
            self._initialize()

        if self.cache_enabled:
            return [
                monster.model_copy(deep=True)
                for monster in self._cache.values()
                if min_cr <= monster.challenge_rating <= max_cr
            ]

        # Without cache, load all and filter
        all_monsters = []
        data = self._load_json_file(self.monsters_file)
        if data and isinstance(data, dict):
            for monster_data in data.get("monsters", []):
                try:
                    monster = self._parse_monster_data(monster_data)
                    if min_cr <= monster.challenge_rating <= max_cr:
                        all_monsters.append(monster)
                except Exception:
                    continue

        return all_monsters

    def get_by_type(self, creature_type: str) -> list[NPCSheet]:
        """Get all monsters of a specific type.

        Args:
            creature_type: Type of creature (e.g., "humanoid", "beast", "undead")

        Returns:
            List of monsters matching the type
        """
        if not self._initialized:
            self._initialize()

        creature_type_lower = creature_type.lower()

        if self.cache_enabled:
            return [
                monster.model_copy(deep=True)
                for monster in self._cache.values()
                if creature_type_lower in monster.type.lower()
            ]

        # Without cache, load all and filter
        all_monsters = []
        data = self._load_json_file(self.monsters_file)
        if data and isinstance(data, dict):
            for monster_data in data.get("monsters", []):
                try:
                    if creature_type_lower in monster_data.get("type", "").lower():
                        monster = self._parse_monster_data(monster_data)
                        all_monsters.append(monster)
                except Exception:
                    continue

        return all_monsters
