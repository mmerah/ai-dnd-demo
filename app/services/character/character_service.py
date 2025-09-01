"""Service for managing character data."""

import logging
from pathlib import Path

from app.interfaces.services import (
    ICharacterService,
    IItemRepository,
    ILoader,
    IPathResolver,
    ISpellRepository,
)
from app.models.character import CharacterSheet

logger = logging.getLogger(__name__)


class CharacterService(ICharacterService):
    """Service for loading and managing character data."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        character_loader: ILoader[CharacterSheet],
        item_repository: IItemRepository | None = None,
        spell_repository: ISpellRepository | None = None,
    ):
        """
        Initialize character service.

        Args:
            path_resolver: Service for resolving file paths
            character_loader: Loader for character data
            item_repository: Repository for validating item references (optional)
            spell_repository: Repository for validating spell references (optional)
        """
        self.path_resolver = path_resolver
        self.character_loader = character_loader
        self.item_repository = item_repository
        self.spell_repository = spell_repository
        self._characters: dict[str, CharacterSheet] = {}
        self._load_all_characters()

    def _load_all_characters(self) -> None:
        """Load all available characters from data directory."""
        # Load from individual character files in characters directory
        characters_dir = self.path_resolver.get_data_dir() / "characters"
        if characters_dir.exists() and characters_dir.is_dir():
            for character_file in characters_dir.glob("*.json"):
                self._load_character_from_file(character_file)

    def _load_character_from_file(self, file_path: Path) -> None:
        """
        Load a single character from a JSON file.

        Args:
            file_path: Path to character JSON file
        """
        try:
            character = self.character_loader.load(file_path)

            # Ensure character has an ID
            if not hasattr(character, "id") or not character.id:
                character.id = file_path.stem

            # Validate references if repositories are available
            if self.item_repository or self.spell_repository:
                errors = self.validate_character_references(character)
                if errors:
                    error_msg = f"Character '{character.id}' has invalid references:\n"
                    for error in errors:
                        error_msg += f"  - {error}\n"
                    raise ValueError(error_msg)

            self._characters[character.id] = character

        except (ValueError, TypeError) as e:
            # Re-raise validation errors with character context
            raise ValueError(f"Failed to load character from {file_path}: {e}") from e
        except Exception as e:
            # Only catch truly unexpected errors (file IO, JSON parsing)
            raise RuntimeError(f"Failed to load character from {file_path}: {e}") from e

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
        Validate that all item and spell references in the character exist.

        Args:
            character: Character to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate inventory items
        if self.item_repository:
            for item in character.inventory:
                if not self.item_repository.validate_reference(item.name):
                    errors.append(f"Unknown item: {item.name}")

        # Validate known spells
        if self.spell_repository and character.spellcasting:
            for spell_name in character.spellcasting.spells_known:
                if not self.spell_repository.validate_reference(spell_name):
                    errors.append(f"Unknown spell: {spell_name}")

        return errors
