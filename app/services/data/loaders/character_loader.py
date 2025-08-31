"""Loader for character data files."""

from pathlib import Path
from typing import Any

from app.models.character import CharacterSheet
from app.services.data.loaders.base_loader import BaseLoader


class CharacterLoader(BaseLoader[CharacterSheet]):
    """Loader for character sheets from JSON files.

    Follows Single Responsibility Principle: only handles character file operations.
    """

    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> CharacterSheet:
        # Any is necessary because raw JSON data can contain mixed types
        """Parse raw JSON data into CharacterSheet model.

        Args:
            data: Raw JSON data from file
            source_path: Path the data was loaded from

        Returns:
            Parsed CharacterSheet

        Raises:
            RuntimeError: If parsing fails
        """
        if not isinstance(data, dict):
            raise RuntimeError(f"Expected dict for character data, got {type(data).__name__} from {source_path}")

        try:
            character = CharacterSheet(**data)
            if self.validate_on_load:
                self._validate_data(character)
            return character
        except Exception as e:
            raise RuntimeError(f"Failed to parse character from {source_path}: {e}") from e

    def _prepare_for_save(self, data: CharacterSheet) -> dict[str, Any]:
        # Any is necessary for JSON-serializable output
        """Prepare character data for JSON serialization.

        Args:
            data: CharacterSheet to save

        Returns:
            JSON-serializable dictionary
        """
        return data.model_dump(mode="json")

    def load_all_characters(self, directory: Path) -> dict[str, CharacterSheet]:
        """Load all character files from a directory.

        Args:
            directory: Directory containing character JSON files

        Returns:
            Dictionary mapping character IDs to CharacterSheet objects
        """
        return self.load_multiple(directory, "*.json")
