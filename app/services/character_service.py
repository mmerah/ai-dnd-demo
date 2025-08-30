"""Service for managing character data."""

import json
from pathlib import Path
from typing import Any

from app.interfaces.services import ICharacterService, IDataService
from app.models.character import CharacterSheet


class CharacterService(ICharacterService):
    """Service for loading and managing character data."""

    def __init__(self, data_service: IDataService | None = None, data_directory: Path | None = None):
        """
        Initialize character service.

        Args:
            data_service: Data service for validating references (optional, validation skipped if None)
            data_directory: Path to data directory containing characters
        """
        if data_directory is None:
            # Default to app/data directory
            data_directory = Path(__file__).parent.parent / "data"
        self.data_directory = data_directory
        self.data_service = data_service
        self._characters: dict[str, CharacterSheet] = {}
        self._load_all_characters()

    def _load_all_characters(self) -> None:
        """Load all available characters from data directory."""
        # Load from the main characters.json file
        characters_file = self.data_directory / "characters.json"
        if characters_file.exists():
            self._load_characters_from_file(characters_file)

        # Also check for a characters directory with individual character files
        characters_dir = self.data_directory / "characters"
        if characters_dir.exists() and characters_dir.is_dir():
            for character_file in characters_dir.glob("*.json"):
                self._load_character_from_file(character_file)

    def _load_characters_from_file(self, file_path: Path) -> None:
        """
        Load characters from a JSON file containing multiple characters.

        Args:
            file_path: Path to characters JSON file
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Handle both single character and multiple characters formats
            if "characters" in data:
                # Multiple characters format
                for char_data in data["characters"]:
                    self._process_character_data(char_data)
            elif "id" in data and "name" in data:
                # Single character format
                self._process_character_data(data)

        except (ValueError, TypeError):
            # Re-raise validation and type errors (fail fast)
            raise
        except Exception as e:
            # Only catch truly unexpected errors (file IO, JSON parsing)
            print(f"Failed to load characters from {file_path}: {e}")

    def _load_character_from_file(self, file_path: Path) -> None:
        """
        Load a single character from a JSON file.

        Args:
            file_path: Path to character JSON file
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Add ID based on filename if not present
            if "id" not in data:
                data["id"] = file_path.stem

            self._process_character_data(data)

        except (ValueError, TypeError):
            # Re-raise validation and type errors (fail fast)
            raise
        except Exception as e:
            # Only catch truly unexpected errors (file IO, JSON parsing)
            print(f"Failed to load character from {file_path}: {e}")

    def _process_character_data(self, char_data: dict[str, Any]) -> None:
        """
        Process and validate a character data dictionary.

        Args:
            char_data: Character data dictionary
        """
        # Using Any here is unavoidable since we're unpacking JSON data directly into a Pydantic model
        # The CharacterSheet model will handle validation of the actual types
        try:
            character = CharacterSheet(**char_data)

            # Validate references if data service is available
            if self.data_service:
                errors = self.validate_character_references(character)
                if errors:
                    error_msg = f"Character '{character.id}' has invalid references:\n"
                    for error in errors:
                        error_msg += f"  - {error}\n"
                    raise ValueError(error_msg)

            self._characters[character.id] = character

        except (ValueError, TypeError) as e:
            # Re-raise validation errors with character context
            raise ValueError(f"Failed to load character '{char_data.get('id', 'unknown')}': {e}") from e

    def get_character(self, character_id: str) -> CharacterSheet | None:
        """
        Get a character by ID.

        Args:
            character_id: ID of the character to retrieve

        Returns:
            CharacterSheet object or None if not found
        """
        return self._characters.get(character_id)

    def list_characters(self) -> list[CharacterSheet]:
        """
        List all available characters.

        Returns:
            List of CharacterSheet objects
        """
        return list(self._characters.values())

    def get_all_characters(self) -> list[CharacterSheet]:
        """
        Get all loaded characters.

        Returns:
            List of all CharacterSheet objects
        """
        return list(self._characters.values())

    def validate_character_references(self, character: CharacterSheet) -> list[str]:
        """
        Validate all item and spell references in a character.
        Checks that all referenced items and spells actually exist in the data service.

        Args:
            character: The character to validate

        Returns:
            List of validation error messages
        """
        if not self.data_service:
            return []

        errors = []

        # Validate inventory items
        for item in character.inventory:
            if not self.data_service.validate_item_reference(item.name):
                errors.append(f"Inventory item '{item.name}' not found in database")

        # Validate spells
        if character.spellcasting and character.spellcasting.spells_known:
            for spell_name in character.spellcasting.spells_known:
                if not self.data_service.validate_spell_reference(spell_name):
                    errors.append(f"Spell '{spell_name}' not found in database")

        return errors
