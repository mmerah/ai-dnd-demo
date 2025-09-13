"""Repository for managing monster definitions."""

import logging
from typing import Any

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.common import IContentPackRegistry, IPathResolver
from app.interfaces.services.data import IRepository
from app.models.alignment import Alignment
from app.models.attributes import SkillValue
from app.models.condition import Condition
from app.models.language import Language
from app.models.monster import MonsterSheet
from app.models.skill import Skill
from app.services.data.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MonsterRepository(BaseRepository[MonsterSheet]):
    """Repository for loading and managing monster data."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        language_repository: IRepository[Language],
        condition_repository: IRepository[Condition],
        alignment_repository: IRepository[Alignment],
        skill_repository: IRepository[Skill],
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        """Initialize the monster repository.

        Args:
            path_resolver: Service for resolving file paths
            language_repository: Repository for languages
            condition_repository: Repository for conditions
            alignment_repository: Repository for alignments
            skill_repository: Repository for skills
            cache_enabled: Whether to cache monsters in memory
            content_pack_registry: Registry for managing content packs
            content_packs: List of content pack IDs to load from
        """
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver
        self.language_repository = language_repository
        self.condition_repository = condition_repository
        self.alignment_repository = alignment_repository
        self.skill_repository = skill_repository

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "monsters"

    def _parse_item(self, data: dict[str, Any]) -> MonsterSheet:
        """Parse raw item data into model instance."""
        return self._parse_monster_data(data)

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
        """Parse monster data from JSON into Monster model."""
        try:
            # Parse skills to list of SkillValue
            data["skills"] = self._parse_skills(data.get("skills"))

            # Create MonsterSheet from data (model validators normalize attacks/languages/HP)
            monster = MonsterSheet(**data)

            # Validate alignment
            if not self.alignment_repository.validate_reference(monster.alignment):
                raise ValueError(f"Monster {monster.name} has unknown alignment: {monster.alignment}")

            # Validate languages
            for lang in monster.languages:
                if not self.language_repository.validate_reference(lang):
                    raise ValueError(f"Monster {monster.name} has unknown language: {lang}")

            # Validate condition immunities
            for cond in monster.condition_immunities:
                if not self.condition_repository.validate_reference(cond):
                    raise ValueError(f"Monster {monster.name} has unknown condition immunity: {cond}")

            return monster
        except Exception as e:
            raise ValueError(f"Failed to parse monster data: {e}") from e

    def get(self, key: str) -> MonsterSheet:
        """Get a monster by index, returning a deep copy.

        Override base implementation to return deep copies to avoid
        modifying the cached version.

        Args:
            key: Monster index to get

        Returns:
            Deep copy of MonsterSheet

        Raises:
            RepositoryNotFoundError: If the monster is not found
        """
        monster = super().get(key)
        # Return a deep copy to avoid modifying the cached version
        return monster.model_copy(deep=True)
