from abc import ABC, abstractmethod

from app.models.attributes import Abilities, AbilityModifiers, AttackAction, SavingThrows, SkillValue
from app.models.character import CharacterSheet
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState
from app.models.item import InventoryItem


class ICharacterService(ABC):
    """Interface for managing character data."""

    @abstractmethod
    def get_character(self, character_id: str) -> CharacterSheet | None:
        pass

    @abstractmethod
    def get_all_characters(self) -> list[CharacterSheet]:
        pass

    @abstractmethod
    def validate_character_references(self, character: CharacterSheet) -> list[str]:
        pass


class ICharacterComputeService(ABC):
    """Interface for computing derived character values (SOLID + DRY).

    Designed to work with EntityState/CharacterInstance/NPCInstance by
    consuming Abilities, level, and class_index to produce derived
    numbers such as proficiency, saves, skills, AC, initiative, and
    spell DC/attack.
    """

    @abstractmethod
    def compute_ability_modifiers(self, abilities: Abilities) -> AbilityModifiers:
        pass

    @abstractmethod
    def compute_proficiency_bonus(self, level: int) -> int:
        pass

    @abstractmethod
    def compute_saving_throws(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> SavingThrows:
        pass

    @abstractmethod
    def compute_skills(
        self,
        class_index: str,
        selected_skills: list[str],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[SkillValue]:
        pass

    @abstractmethod
    def compute_armor_class(self, modifiers: AbilityModifiers, inventory: list[InventoryItem]) -> int:
        pass

    @abstractmethod
    def compute_initiative_bonus(self, modifiers: AbilityModifiers) -> int:
        pass

    @abstractmethod
    def compute_spell_numbers(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        """Returns (spell_save_dc, spell_attack_bonus)."""
        pass

    @abstractmethod
    def compute_speed(self, race_index: str, inventory: list[InventoryItem]) -> int:
        """Compute base speed from race; minimal rule ignores armor penalties for now."""
        pass

    @abstractmethod
    def compute_hit_points_and_dice(self, class_index: str, level: int, con_modifier: int) -> tuple[int, int, str]:
        """Compute base maximum HP and hit dice for a class/level.

        Returns a tuple of (max_hp, hit_dice_total, hit_die_type), where hit_die_type is like 'd8'.
        Uses level 1 max hit die + CON mod, and average per-level increase thereafter with a minimum of 1 per level.
        """
        pass

    @abstractmethod
    def initialize_entity_state(self, sheet: CharacterSheet) -> EntityState:
        """Create an EntityState from a CharacterSheet's starting_* fields."""
        pass

    @abstractmethod
    def recompute_entity_state(self, sheet: CharacterSheet, state: EntityState) -> EntityState:
        """Recompute derived fields on EntityState from sheet + current state.

        Preserves current HP (clamped to new max) and current hit dice count (clamped to total).
        """
        pass

    @abstractmethod
    def compute_attacks(
        self,
        class_index: str,
        race_index: str,
        inventory: list[InventoryItem],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[AttackAction]:
        """Compute available attacks from equipped weapons or provide an unarmed strike.

        Uses simple proficiency heuristics (class/race proficiencies) and weapon properties
        to select the attack ability (STR/DEX) and to-hit/damage values.
        """
        pass

    @abstractmethod
    def set_item_equipped(self, state: EntityState, item_name: str, equipped: bool) -> EntityState:
        """Equip or unequip an inventory item by name.

        Validates equippability against the item repository, performs stack split/merge
        for multi-quantity items, and returns the updated EntityState.

        Constraints (enforced):
        - Only one shield may be equipped at a time
        - Only one body armor (light/medium/heavy) may be equipped at a time
        - Operation equips/unequips exactly one unit per call

        Args:
            state: Current entity state
            item_name: Name of the item to equip/unequip
            equipped: True to equip, False to unequip

        Returns:
            Updated EntityState with item equipped/unequipped

        Raises:
            ValueError: If item not found, not equippable, or constraints violated
        """
        pass


class ILevelProgressionService(ABC):
    """Interface for minimal character level-up progression."""

    @abstractmethod
    def level_up_character(self, character: CharacterInstance) -> None:
        """Increment level and adjust HP/Hit Dice, then recompute derived values."""
        pass
