"""Service for managing character data."""

import logging
from pathlib import Path

from app.interfaces.services.character import ICharacterComputeService, ICharacterService
from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import ILoader, IRepository
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition
from app.models.character import CharacterSheet, Currency
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.equipment_slots import EquipmentSlotType
from app.models.feat import FeatDefinition
from app.models.feature import FeatureDefinition
from app.models.game_state import GameState
from app.models.instances.entity_state import EntityState
from app.models.item import InventoryItem, ItemDefinition, ItemRarity, ItemType
from app.models.language import Language
from app.models.race import RaceDefinition, SubraceDefinition
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition

logger = logging.getLogger(__name__)


class CharacterService(ICharacterService):
    """Service for loading and managing character data."""

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
        Initialize character service.

        Args:
            path_resolver: Service for resolving file paths
            character_loader: Loader for character data
            compute_service: Service for computing character values
            item_repository: Repository for validating item references (optional)
            spell_repository: Repository for validating spell references (optional)
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

    def _resolve_entity(self, game_state: GameState, entity_id: str | None) -> tuple[EntityState, bool]:
        """Resolve an entity by ID, handling player ID matching.

        Args:
            game_state: Current game state
            entity_id: Entity ID (None or player's ID for player)

        Returns:
            Tuple of (entity_state, is_player)

        Raises:
            ValueError: If entity not found
        """
        # Check if this is the player (None or matching player's instance_id)
        if entity_id is None or entity_id == game_state.character.instance_id:
            return game_state.character.state, True

        # Try NPCs first
        npc = next((n for n in game_state.npcs if n.instance_id == entity_id), None)
        if npc:
            return npc.state, False

        # Try monsters
        monster = next((m for m in game_state.monsters if m.instance_id == entity_id), None)
        if monster:
            return monster.state, False

        raise ValueError(f"Entity '{entity_id}' not found")

    def recompute_character_state(self, game_state: GameState) -> None:
        char = game_state.character
        new_state = self.compute_service.recompute_entity_state(game_state, char.sheet, char.state)
        char.state = new_state
        char.touch()

    def equip_item(
        self,
        game_state: GameState,
        entity_id: str | None,
        item_index: str,
        slot: EquipmentSlotType | None = None,
        unequip: bool = False,
    ) -> None:
        # Check if this is the player (None or matching player's instance_id)
        if entity_id is None or entity_id == game_state.character.instance_id:
            state = game_state.character.state
            updated = self.compute_service.equip_item_to_slot(game_state, state, item_index, slot, unequip)
            game_state.character.state = updated
            game_state.character.touch()
        else:
            # NPC only, monsters don't have equipment
            npc = next((n for n in game_state.npcs if n.instance_id == entity_id), None)
            if not npc:
                raise ValueError(f"Entity '{entity_id}' not found")
            updated = self.compute_service.equip_item_to_slot(game_state, npc.state, item_index, slot, unequip)
            npc.state = updated

    def modify_currency(
        self,
        game_state: GameState,
        entity_id: str | None,
        gold: int = 0,
        silver: int = 0,
        copper: int = 0,
    ) -> tuple[Currency, Currency]:
        state, is_player = self._resolve_entity(game_state, entity_id)

        # Capture old values
        old_currency = Currency(
            gold=state.currency.gold,
            silver=state.currency.silver,
            copper=state.currency.copper,
        )

        # Apply changes
        state.currency.gold = max(0, state.currency.gold + gold)
        state.currency.silver = max(0, state.currency.silver + silver)
        state.currency.copper = max(0, state.currency.copper + copper)

        # Capture new values
        new_currency = Currency(
            gold=state.currency.gold,
            silver=state.currency.silver,
            copper=state.currency.copper,
        )

        if is_player:
            game_state.character.touch()

        return old_currency, new_currency

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

    def update_hp(
        self,
        game_state: GameState,
        entity_id: str | None,
        amount: int,
    ) -> tuple[int, int, int]:
        state, is_player = self._resolve_entity(game_state, entity_id)

        # Normalize entity_id for combat tracking
        if is_player:
            entity_id = game_state.character.instance_id

        old_hp = state.hit_points.current
        max_hp = state.hit_points.maximum
        new_hp = min(old_hp + amount, max_hp) if amount > 0 else max(0, old_hp + amount)
        state.hit_points.current = new_hp

        # Update combat participant active status if in combat and HP reaches 0
        if game_state.combat.is_active and new_hp == 0:
            for participant in game_state.combat.participants:
                if participant.entity_id == entity_id:
                    participant.is_active = False
                    logger.debug(f"Combat participant {participant.name} marked as inactive (0 HP)")
                    break

        if is_player:
            game_state.character.touch()

        return old_hp, new_hp, max_hp

    def add_condition(
        self,
        game_state: GameState,
        entity_id: str | None,
        condition: str,
    ) -> bool:
        state, is_player = self._resolve_entity(game_state, entity_id)

        if condition not in state.conditions:
            state.conditions.append(condition)
            if is_player:
                game_state.character.touch()
            return True
        return False

    def remove_condition(
        self,
        game_state: GameState,
        entity_id: str | None,
        condition: str,
    ) -> bool:
        state, is_player = self._resolve_entity(game_state, entity_id)

        if condition in state.conditions:
            state.conditions.remove(condition)
            if is_player:
                game_state.character.touch()
            return True
        return False

    def update_spell_slots(
        self,
        game_state: GameState,
        level: int,
        amount: int,
    ) -> tuple[int, int, int]:
        character = game_state.character.state

        if not character.spellcasting:
            raise ValueError("Character has no spellcasting ability")

        spell_slots = character.spellcasting.spell_slots

        if level not in spell_slots:
            raise ValueError(f"No spell slots for level {level}")

        slot = spell_slots[level]
        old_slots = slot.current
        slot.current = max(0, min(slot.total, old_slots + amount))
        new_slots = slot.current
        max_slots = slot.total

        game_state.character.touch()

        return old_slots, new_slots, max_slots
