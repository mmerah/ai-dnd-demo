"""Loader for character data files."""

from pathlib import Path
from typing import Any

from app.models.character import CharacterSheet
from app.services.data.loaders.base_loader import BaseLoader


class CharacterLoader(BaseLoader[CharacterSheet]):
    """Loader for character sheets from JSON files."""

    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> CharacterSheet:
        # Any is necessary because raw JSON data can contain mixed types
        if not isinstance(data, dict):
            raise RuntimeError(f"Expected dict for character data, got {type(data).__name__} from {source_path}")

        try:
            character = CharacterSheet(**data)
            if self.validate_on_load:
                self._validate_data(character)
            return character
        except Exception as e:
            raise RuntimeError(f"Failed to parse character from {source_path}: {e}") from e
