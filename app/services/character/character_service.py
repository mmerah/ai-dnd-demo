"""Service for managing character sheet data (loading and validation)."""

import logging
from pathlib import Path

from app.interfaces.services.character import ICharacterComputeService, ICharacterService
from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import ILoader, IRepository
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition
from app.models.character import CharacterSheet
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.feat import FeatDefinition
from app.models.feature import FeatureDefinition
from app.models.game_state import GameState
from app.models.item import InventoryItem, ItemDefinition, ItemRarity, ItemType
from app.models.language import Language
from app.models.race import RaceDefinition, SubraceDefinition
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition

logger = logging.getLogger(__name__)


class CharacterSheetService(ICharacterService):
    """Service for loading and validating character sheet data.

    This service focuses solely on character sheet management (loading, validation,
    and template operations). Runtime state mutations are handled by EntityStateService.
    """

    def __init__(
        self,
        path_resolver: IPathResolver,
        character_loader: ILoader[CharacterSheet],
        compute_service: ICharacterComputeService,
        item_repository: IRepository[ItemDefinition],
        spell_repository: IRepository[SpellDefinition],
        alignment_repository: IRepository[Alignment],
        class_repository: IRepository[ClassDefinition],
        subclass_repository: IRepository[SubclassDefinition],
        language_repository: IRepository[Language],
        race_repository: IRepository[RaceDefinition],
        race_subrace_repository: IRepository[SubraceDefinition],
        background_repository: IRepository[BackgroundDefinition],
        skill_repository: IRepository[Skill],
        trait_repository: IRepository[TraitDefinition],
        feature_repository: IRepository[FeatureDefinition],
        feat_repository: IRepository[FeatDefinition],
    ):
        """
        Initialize character sheet service.

        Args:
            path_resolver: Service for resolving file paths
            character_loader: Loader for character data
            compute_service: Service for computing character values
            item_repository: Repository for validating item references
            spell_repository: Repository for validating spell references
            alignment_repository: Repository for validating alignments
            class_repository: Repository for validating classes
            subclass_repository: Repository for validating subclasses
            language_repository: Repository for validating languages
            race_repository: Repository for validating races
            race_subrace_repository: Repository for validating subraces
            background_repository: Repository for validating backgrounds
            skill_repository: Repository for validating skills
            trait_repository: Repository for validating traits
            feature_repository: Repository for validating features
            feat_repository: Repository for validating feats
        """
        self.path_resolver = path_resolver
        self.character_loader = character_loader
        self.compute_service = compute_service
        self.item_repository = item_repository
        self.spell_repository = spell_repository
        self.alignment_repository = alignment_repository
        self.class_repository = class_repository
        self.subclass_repository = subclass_repository
        self.language_repository = language_repository
        self.race_repository = race_repository
        self.race_subrace_repository = race_subrace_repository
        self.background_repository = background_repository
        self.skill_repository = skill_repository
        self.trait_repository = trait_repository
        self.feature_repository = feature_repository
        self.feat_repository = feat_repository
        self._characters: dict[str, CharacterSheet] = {}
        self._load_all_characters()

    def _load_all_characters(self) -> None:
        """Load all available characters from data directory."""
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

            # CharacterSheet model always has an id field
            if not character.id:
                character.id = file_path.stem

            errors = self.validate_character_references(character)
            if errors:
                error_msg = f"Character '{character.id}' has invalid references:\n"
                for error in errors:
                    error_msg += f"  - {error}\n"
                raise ValueError(error_msg)

            self._characters[character.id] = character

        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to load character from {file_path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load character from {file_path}: {e}") from e

    def get_character(self, character_id: str) -> CharacterSheet | None:
        return self._characters.get(character_id)

    def get_all_characters(self) -> list[CharacterSheet]:
        return list(self._characters.values())

    def validate_character_references(self, character: CharacterSheet) -> list[str]:
        errors = []

        # Validate starting inventory items
        for item in character.starting_inventory:
            if not self.item_repository.validate_reference(item.index):
                errors.append(f"Unknown item: {item.index}")

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

    def create_placeholder_item(
        self,
        game_state: GameState,
        item_index: str,
        quantity: int = 1,
    ) -> InventoryItem:
        # Use index as name for placeholder items
        item_name = item_index.replace("-", " ").title()
        item_def = ItemDefinition(
            index=item_index,
            name=item_name,
            type=ItemType.ADVENTURING_GEAR,
            rarity=ItemRarity.COMMON,
            description=f"A unique item: {item_name}",
            weight=0.5,
            value=1,
            content_pack="sandbox",
        )
        return InventoryItem.from_definition(item_def, quantity=quantity)
