"""Service for managing character data."""

import logging
from pathlib import Path

from app.interfaces.services.character import ICharacterService
from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import IItemRepository, ILoader, ISpellRepository
from app.models.character import CharacterSheet
from app.services.data.repositories.alignment_repository import AlignmentRepository
from app.services.data.repositories.background_repository import BackgroundRepository
from app.services.data.repositories.class_repository import ClassRepository, SubclassRepository
from app.services.data.repositories.condition_repository import ConditionRepository
from app.services.data.repositories.damage_type_repository import DamageTypeRepository
from app.services.data.repositories.feat_repository import FeatRepository
from app.services.data.repositories.feature_repository import FeatureRepository
from app.services.data.repositories.language_repository import LanguageRepository
from app.services.data.repositories.race_repository import RaceRepository
from app.services.data.repositories.race_repository import SubraceRepository as RaceSubraceRepository
from app.services.data.repositories.skill_repository import SkillRepository
from app.services.data.repositories.trait_repository import TraitRepository
from app.services.data.repositories.weapon_property_repository import WeaponPropertyRepository

logger = logging.getLogger(__name__)


class CharacterService(ICharacterService):
    """Service for loading and managing character data."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        character_loader: ILoader[CharacterSheet],
        item_repository: IItemRepository,
        spell_repository: ISpellRepository,
        alignment_repository: AlignmentRepository,
        class_repository: ClassRepository,
        subclass_repository: SubclassRepository,
        language_repository: LanguageRepository,
        condition_repository: ConditionRepository,
        race_repository: RaceRepository,
        race_subrace_repository: RaceSubraceRepository,
        background_repository: BackgroundRepository,
        skill_repository: SkillRepository,
        trait_repository: TraitRepository,
        feature_repository: FeatureRepository,
        feat_repository: FeatRepository,
        damage_type_repository: DamageTypeRepository,
        weapon_property_repository: WeaponPropertyRepository,
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
        self.alignment_repository = alignment_repository
        self.class_repository = class_repository
        self.subclass_repository = subclass_repository
        self.language_repository = language_repository
        self.condition_repository = condition_repository
        self.race_repository = race_repository
        self.race_subrace_repository = race_subrace_repository
        self.background_repository = background_repository
        self.skill_repository = skill_repository
        self.trait_repository = trait_repository
        self.feature_repository = feature_repository
        self.feat_repository = feat_repository
        self.damage_type_repository = damage_type_repository
        self.weapon_property_repository = weapon_property_repository
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

            # Ensure character has a non-empty ID
            # CharacterSheet model always has an id field
            if not character.id:
                character.id = file_path.stem

            # Always validate references (fail-fast)
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

        # Validate starting inventory items
        for item in character.starting_inventory:
            if not self.item_repository.validate_reference(item.name):
                errors.append(f"Unknown item: {item.name}")

        # Validate known spells
        starting_sc = character.starting_spellcasting
        if starting_sc:
            for spell_name in starting_sc.spells_known:
                if not self.spell_repository.validate_reference(spell_name):
                    errors.append(f"Unknown spell: {spell_name}")

        # Validate selected skills (optional)
        for sk in character.starting_skill_indexes:
            if not self.skill_repository.validate_reference(sk):
                errors.append(f"Unknown skill index: {sk}")

        # Validate alignment index
        if character.alignment and not self.alignment_repository.validate_reference(character.alignment):
            errors.append(f"Unknown alignment index: {character.alignment}")

        # Validate class and subclass indexes
        if character.class_index and not self.class_repository.validate_reference(character.class_index):
            errors.append(f"Unknown class index: {character.class_index}")
        if character.subclass:
            if not self.subclass_repository.validate_reference(character.subclass):
                errors.append(f"Unknown subclass index: {character.subclass}")
            else:
                # Ensure subclass parent matches class_index if both available
                if character.class_index:
                    subclass_def = self.subclass_repository.get(character.subclass)
                    if subclass_def.parent_class != character.class_index:
                        errors.append(
                            f"Subclass '{character.subclass}' does not belong to class '{character.class_index}'"
                        )

        # Validate languages
        if character.languages:
            for lang in character.languages:
                if not self.language_repository.validate_reference(lang):
                    errors.append(f"Unknown language index: {lang}")

        # Validate race and subrace
        if character.race and not self.race_repository.validate_reference(character.race):
            errors.append(f"Unknown race index: {character.race}")
        if character.subrace:
            if not self.race_subrace_repository.validate_reference(character.subrace):
                errors.append(f"Unknown subrace index: {character.subrace}")
            else:
                if character.race:
                    subrace_def = self.race_subrace_repository.get(character.subrace)
                    if subrace_def.parent_race != character.race:
                        errors.append(f"Subrace '{character.subrace}' does not belong to race '{character.race}'")

        # Validate background
        if character.background and not self.background_repository.validate_reference(character.background):
            errors.append(f"Unknown background index: {character.background}")

        # Validate optional catalog references for features/traits/feats
        if character.trait_indexes:
            for t in character.trait_indexes:
                if not self.trait_repository.validate_reference(t):
                    errors.append(f"Unknown trait index: {t}")
        if character.feature_indexes:
            for f in character.feature_indexes:
                if not self.feature_repository.validate_reference(f):
                    errors.append(f"Unknown feature index: {f}")
        if character.feat_indexes:
            for f in character.feat_indexes:
                if not self.feat_repository.validate_reference(f):
                    errors.append(f"Unknown feat index: {f}")

        return errors
