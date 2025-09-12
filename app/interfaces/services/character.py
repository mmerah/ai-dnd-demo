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
        """Get a character by ID.

        Args:
            character_id: ID of the character to retrieve

        Returns:
            CharacterSheet object or None if not found
        """
        pass

    @abstractmethod
    def get_all_characters(self) -> list[CharacterSheet]:
        """Get all loaded characters.

        Returns:
            List of all CharacterSheet objects
        """
        pass

    @abstractmethod
    def validate_character_references(self, character: CharacterSheet) -> list[str]:
        """Validate that all item and spell references in the character exist.

        Args:
            character: Character to validate

        Returns:
            List of validation error messages (empty if all references are valid)
        """
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
        """Compute ability modifiers from ability scores.

        Uses D&D 5e formula: (score - 10) // 2

        Args:
            abilities: Ability scores (STR, DEX, CON, INT, WIS, CHA)

        Returns:
            Computed ability modifiers
        """
        pass

    @abstractmethod
    def compute_proficiency_bonus(self, level: int) -> int:
        """Compute proficiency bonus based on character level.

        Uses D&D 5e progression:
        - Levels 1-4: +2
        - Levels 5-8: +3
        - Levels 9-12: +4
        - Levels 13-16: +5
        - Levels 17+: +6

        Args:
            level: Character level

        Returns:
            Proficiency bonus
        """
        pass

    @abstractmethod
    def compute_saving_throws(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> SavingThrows:
        """Compute saving throw bonuses based on class proficiencies.

        Args:
            class_index: Character class identifier
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            Saving throw bonuses for all abilities
        """
        pass

    @abstractmethod
    def compute_skills(
        self,
        class_index: str,
        selected_skills: list[str],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[SkillValue]:
        """Compute skill bonuses based on proficiencies and ability modifiers.

        If no skills are explicitly selected, picks first allowed skills from
        class proficiency choices.

        Args:
            class_index: Character class identifier
            selected_skills: List of skill indices the character is proficient in
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            List of skill values with computed bonuses
        """
        pass

    @abstractmethod
    def compute_armor_class(self, modifiers: AbilityModifiers, inventory: list[InventoryItem]) -> int:
        """Compute armor class from equipped items and DEX modifier.

        Rules:
        - Base unarmored AC: 10 + DEX modifier
        - Light armor: AC + full DEX modifier
        - Medium armor: AC + DEX modifier (max +2)
        - Heavy armor: AC (no DEX modifier)
        - Shield: +2 AC (stacks with armor)

        Args:
            modifiers: Ability modifiers (uses DEX)
            inventory: List of inventory items (checks equipped armor/shields)

        Returns:
            Computed armor class
        """
        pass

    @abstractmethod
    def compute_initiative_bonus(self, modifiers: AbilityModifiers) -> int:
        """Compute initiative bonus (DEX modifier).

        Args:
            modifiers: Ability modifiers

        Returns:
            Initiative bonus
        """
        pass

    @abstractmethod
    def compute_spell_numbers(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        """Compute spell save DC and spell attack bonus.

        Formulas:
        - Spell Save DC: 8 + proficiency bonus + spellcasting ability modifier
        - Spell Attack Bonus: proficiency bonus + spellcasting ability modifier

        Args:
            class_index: Character class identifier
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            Tuple of (spell_save_dc, spell_attack_bonus), or (None, None) if class
            doesn't have spellcasting
        """
        pass

    @abstractmethod
    def compute_speed(self, race_index: str, inventory: list[InventoryItem]) -> int:
        """Compute base speed from race.

        Note: Current implementation uses base racial speed only.
        Armor penalties are not yet implemented.

        Args:
            race_index: Character race identifier
            inventory: List of inventory items (for future armor penalty checks)

        Returns:
            Movement speed in feet
        """
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
        """Level up a character, adjusting HP, hit dice, and derived values.

        Process:
        1. Increment character level
        2. Increase max HP (average hit die + CON modifier)
        3. Add one hit die to the pool
        4. Recompute all derived values (AC, saves, skills, etc.)

        Args:
            character: Character instance to level up (modified in-place)
        """
        pass
