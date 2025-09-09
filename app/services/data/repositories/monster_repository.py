"""Repository for managing monster definitions."""

import logging
from typing import Any

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import IMonsterRepository, IRepository
from app.models.alignment import Alignment
from app.models.attributes import SkillValue
from app.models.condition import Condition
from app.models.language import Language
from app.models.monster import MonsterSheet
from app.models.skill import Skill
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MonsterRepository(BaseRepository[MonsterSheet], IMonsterRepository):
    """Repository for loading and managing monster data.

    Follows Single Responsibility Principle: only manages monster data access.
    """

    def __init__(
        self,
        path_resolver: IPathResolver,
        language_repository: IRepository[Language],
        condition_repository: IRepository[Condition],
        alignment_repository: IRepository[Alignment],
        skill_repository: IRepository[Skill],
        cache_enabled: bool = True,
    ):
        """Initialize the monster repository.

        Args:
            path_resolver: Service for resolving file paths
            cache_enabled: Whether to cache monsters in memory
        """
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.monsters_file = self.path_resolver.get_shared_data_file("monsters")
        self.language_repository = language_repository
        self.condition_repository = condition_repository
        self.alignment_repository = alignment_repository
        self.skill_repository = skill_repository

    def _initialize(self) -> None:
        """Initialize the repository by loading all monsters if caching is enabled."""
        if self.cache_enabled:
            self._load_all_monsters()
        self._initialized = True

    def _load_all_monsters(self) -> None:
        """Load all monsters from the monsters.json file into cache."""
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            logger.warning("Monsters data file not found or invalid: %s", self.monsters_file)
            return

        for monster_data in data.get("monsters", []):
            try:
                monster = self._parse_monster_data(monster_data)
                self._cache[monster.index] = monster
            except Exception as e:
                # Log error but continue loading other monsters
                logger.warning(f"Failed to load monster {monster_data.get('name', 'unknown')}: {e}")

    def _load_item(self, key: str) -> MonsterSheet | None:
        """Load a single monster by name.

        Args:
            key: Monster name to load

        Returns:
            Monster or None if not found
        """
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            return None

        for monster_data in data.get("monsters", []):
            idx = str(monster_data.get("index", ""))
            if idx.lower() == key.lower():
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

        keys: list[str] = []
        for monster in data.get("monsters", []):
            # Use index as primary key since it's now mandatory
            if "index" in monster:
                keys.append(str(monster["index"]))
        return sorted(keys)

    def _check_key_exists(self, key: str) -> bool:
        """Check if a monster exists without using cache."""
        data = self._load_json_file(self.monsters_file)
        if not data or not isinstance(data, dict):
            return False

        for m in data.get("monsters", []):
            idx = str(m.get("index", ""))
            if idx.lower() == key.lower():
                return True
        return False

    def _parse_skills(self, data: dict[str, int] | None) -> list[SkillValue]:
        """Parse skills from JSON dict to list of SkillValue using repository indexes."""
        if not data:
            return []

        skills = []
        for skill_name, modifier in data.items():
            # Resolve to index via repo (by name or index)
            try:
                skill_def = self.skill_repository.get(skill_name)
            except RepositoryNotFoundError:
                normalized = skill_name.replace(" ", "-").lower()
                try:
                    skill_def = self.skill_repository.get(normalized)
                except RepositoryNotFoundError:
                    logger.warning(f"Unknown skill: {skill_name}")
                    continue
            idx = skill_def.index
            skills.append(SkillValue(index=idx, value=modifier))

        return skills

    def _parse_monster_data(self, data: dict[str, Any]) -> MonsterSheet:
        # Any is necessary because monster data from JSON contains mixed types
        """Parse monster data from JSON into Monster model.

        Args:
            data: Raw monster data from JSON

        Returns:
            Parsed Monster

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

            # Normalize languages to list of indexes
            langs = data.get("languages")
            if isinstance(langs, str):
                # Split by comma and normalize
                parts = [p.strip() for p in langs.split(",") if p and p.strip().lower() != "none"]
                data["languages"] = [p.lower().replace(" ", "-") for p in parts]
            elif langs is None:
                data["languages"] = []

            # Parse skills to list of SkillValue
            data["skills"] = self._parse_skills(data.get("skills"))

            # Create MonsterSheet from data
            monster = MonsterSheet(**data)

            # Validate alignment (fail-fast)
            if not self.alignment_repository.validate_reference(monster.alignment):
                raise ValueError(f"Monster {monster.name} has unknown alignment: {monster.alignment}")

            # Validate languages (fail-fast)
            for lang in monster.languages:
                if not self.language_repository.validate_reference(lang):
                    raise ValueError(f"Monster {monster.name} has unknown language: {lang}")

            # Validate condition immunities (fail-fast)
            for cond in monster.condition_immunities:
                if not self.condition_repository.validate_reference(cond):
                    raise ValueError(f"Monster {monster.name} has unknown condition immunity: {cond}")

            return monster
        except Exception as e:
            raise ValueError(f"Failed to parse monster data: {e}") from e

    def get(self, key: str) -> MonsterSheet:
        """Get a monster by name, returning a deep copy.

        Override base implementation to return deep copies to avoid
        modifying the cached version.

        Args:
            key: Monster name to get

        Returns:
            Deep copy of MonsterSheet

        Raises:
            RepositoryNotFoundError: If the monster is not found
        """
        monster = super().get(key)
        # Return a deep copy to avoid modifying the cached version
        return monster.model_copy(deep=True)

    def get_by_challenge_rating(self, min_cr: float, max_cr: float) -> list[MonsterSheet]:
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
        all_monsters: list[MonsterSheet] = []
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

    def get_by_type(self, creature_type: str) -> list[MonsterSheet]:
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
        all_monsters: list[MonsterSheet] = []
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
