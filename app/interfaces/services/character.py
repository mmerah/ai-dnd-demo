from abc import ABC, abstractmethod

from app.models.attributes import Abilities, AbilityModifiers, AttackAction, SavingThrows, SkillValue
from app.models.character import CharacterSheet, Currency
from app.models.equipment_slots import EquipmentSlotType
from app.models.game_state import GameState
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

    @abstractmethod
    def recompute_character_state(self, game_state: GameState) -> None:
        """Recompute all derived values for the player character.

        Recalculates all computed fields (AC, saves, skills, attacks) based on
        current abilities, level, equipment, and class features. Preserves
        current resource values (HP, spell slots, etc.) while updating maximums.

        Args:
            game_state: Current game state containing the character instance

        Side Effects:
            Modifies the character's state in-place with updated computed values
        """
        pass

    @abstractmethod
    def equip_item(
        self,
        game_state: GameState,
        entity_id: str,
        item_index: str,
        slot: EquipmentSlotType | None = None,
        unequip: bool = False,
    ) -> None:
        """Equip or unequip an item for a character or NPC.

        Handles the equipping/unequipping of items, automatically selecting
        appropriate slots if not specified. Validates item constraints and
        updates computed values (AC, attacks) after equipment changes.

        Args:
            game_state: Current game state
            entity_id: ID of entity to equip
            item_index: Index/ID of the item to equip/unequip
            slot: Target equipment slot (auto-selects if None)
            unequip: If True, removes item from equipment slots

        Raises:
            ValueError: If item not found, not equippable, or slot constraints violated

        Side Effects:
            - Modifies entity's equipment slots
            - Triggers state recomputation for updated AC/attacks
        """
        pass

    @abstractmethod
    def modify_currency(
        self,
        game_state: GameState,
        entity_id: str,
        gold: int = 0,
        silver: int = 0,
        copper: int = 0,
    ) -> tuple[Currency, Currency]:
        """Modify currency for a character or NPC.

        Adds or subtracts currency values, ensuring no negative results.

        Args:
            game_state: Current game state
            entity_id: ID of entity
            gold: Gold pieces to add/subtract
            silver: Silver pieces to add/subtract
            copper: Copper pieces to add/subtract

        Returns:
            Tuple of (old_currency, new_currency)

        Raises:
            ValueError: If entity not found

        Side Effects:
            Modifies entity's currency in-place
        """
        pass

    @abstractmethod
    def create_placeholder_item(
        self,
        game_state: GameState,
        item_index: str,
        quantity: int = 1,
    ) -> InventoryItem:
        """Create a placeholder item for AI-invented items not in repository.

        Creates a basic item definition when the AI references an item
        that doesn't exist in the repository.

        Args:
            game_state: Current game state
            item_index: Index/ID of the item
            quantity: Initial quantity

        Returns:
            Created InventoryItem
        """
        pass

    @abstractmethod
    def update_hp(
        self,
        game_state: GameState,
        entity_id: str,
        amount: int,
    ) -> tuple[int, int, int]:
        """Update HP for an entity.

        Args:
            game_state: Current game state
            entity_id: ID of entity
            amount: HP change (positive for healing, negative for damage)

        Returns:
            Tuple of (old_hp, new_hp, max_hp)

        Raises:
            ValueError: If entity not found

        Side Effects:
            - Modifies entity's HP in-place
            - Updates combat participant active status if HP reaches 0
        """
        pass

    @abstractmethod
    def add_condition(
        self,
        game_state: GameState,
        entity_id: str,
        condition: str,
    ) -> bool:
        """Add a condition to an entity.

        Args:
            game_state: Current game state
            entity_id: ID of entity
            condition: Condition to add

        Returns:
            True if condition was added (not already present)

        Raises:
            ValueError: If entity not found

        Side Effects:
            Modifies entity's conditions list
        """
        pass

    @abstractmethod
    def remove_condition(
        self,
        game_state: GameState,
        entity_id: str,
        condition: str,
    ) -> bool:
        """Remove a condition from an entity.

        Args:
            game_state: Current game state
            entity_id: ID of entity
            condition: Condition to remove

        Returns:
            True if condition was removed (was present)

        Raises:
            ValueError: If entity not found

        Side Effects:
            Modifies entity's conditions list
        """
        pass

    @abstractmethod
    def update_spell_slots(
        self,
        game_state: GameState,
        level: int,
        amount: int,
    ) -> tuple[int, int, int]:
        """Update spell slots for the player character.

        Args:
            game_state: Current game state
            level: Spell level
            amount: Slot change (positive to restore, negative to use)

        Returns:
            Tuple of (old_slots, new_slots, max_slots)

        Raises:
            ValueError: If character has no spellcasting or invalid level

        Side Effects:
            Modifies character's spell slots
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
        self, game_state: GameState, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> SavingThrows:
        """Compute saving throw bonuses based on class proficiencies.

        Args:
            game_state: Game state for pack-scoped repository access
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
        game_state: GameState,
        class_index: str,
        selected_skills: list[str],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[SkillValue]:
        """Compute skill bonuses based on proficiencies and ability modifiers.

        If no skills are explicitly selected, picks first allowed skills from
        class proficiency choices.

        Args:
            game_state: Game state for pack-scoped repository access
            class_index: Character class identifier
            selected_skills: List of skill indices the character is proficient in
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            List of skill values with computed bonuses
        """
        pass

    @abstractmethod
    def compute_armor_class(self, game_state: GameState, modifiers: AbilityModifiers, state: EntityState) -> int:
        """Compute armor class from equipped items and DEX modifier.

        Rules:
        - Base unarmored AC: 10 + DEX modifier
        - Light armor: AC + full DEX modifier
        - Medium armor: AC + DEX modifier (max +2)
        - Heavy armor: AC (no DEX modifier)
        - Shield: +2 AC (stacks with armor)

        Args:
            game_state: Game state for pack-scoped repository access
            modifiers: Ability modifiers (uses DEX)
            state: Entity state with equipment slots

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
        self, game_state: GameState, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        """Compute spell save DC and spell attack bonus.

        Formulas:
        - Spell Save DC: 8 + proficiency bonus + spellcasting ability modifier
        - Spell Attack Bonus: proficiency bonus + spellcasting ability modifier

        Args:
            game_state: Game state for pack-scoped repository access
            class_index: Character class identifier
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            Tuple of (spell_save_dc, spell_attack_bonus), or (None, None) if class
            doesn't have spellcasting
        """
        pass

    @abstractmethod
    def compute_speed(self, game_state: GameState, race_index: str, inventory: list[InventoryItem]) -> int:
        """Compute base speed from race.

        Note: Current implementation uses base racial speed only.
        Armor penalties are not yet implemented.

        Args:
            game_state: Game state for pack-scoped repository access
            race_index: Character race identifier
            inventory: List of inventory items (for future armor penalty checks)

        Returns:
            Movement speed in feet
        """
        pass

    @abstractmethod
    def compute_hit_points_and_dice(
        self, game_state: GameState, class_index: str, level: int, con_modifier: int
    ) -> tuple[int, int, str]:
        """Compute base maximum HP and hit dice for a class/level.

        Args:
            game_state: Game state for pack-scoped repository access
            class_index: Character class identifier
            level: Character level
            con_modifier: Constitution modifier

        Returns:
            Tuple of (max_hp, hit_dice_total, hit_die_type), where hit_die_type is like 'd8'.
            Uses level 1 max hit die + CON mod, and average per-level increase thereafter with a minimum of 1 per level.
        """
        pass

    @abstractmethod
    def initialize_entity_state(self, game_state: GameState, sheet: CharacterSheet) -> EntityState:
        """Create an EntityState from a CharacterSheet's starting_* fields.

        Args:
            game_state: Game state for pack-scoped repository access
            sheet: Character sheet to initialize from

        Returns:
            Initialized EntityState with computed values
        """
        pass

    @abstractmethod
    def recompute_entity_state(self, game_state: GameState, sheet: CharacterSheet, state: EntityState) -> EntityState:
        """Recompute derived fields on EntityState from sheet + current state.

        Preserves current HP (clamped to new max) and current hit dice count (clamped to total).

        Args:
            game_state: Game state for pack-scoped repository access
            sheet: Character sheet
            state: Current entity state

        Returns:
            Updated EntityState with recomputed derived values
        """
        pass

    @abstractmethod
    def compute_attacks(
        self,
        game_state: GameState,
        class_index: str,
        race_index: str,
        state: EntityState,
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[AttackAction]:
        """Compute available attacks from equipped weapons or provide an unarmed strike.

        Uses simple proficiency heuristics (class/race proficiencies) and weapon properties
        to select the attack ability (STR/DEX) and to-hit/damage values.

        Args:
            game_state: Game state for pack-scoped repository access
            class_index: Character class identifier
            race_index: Character race identifier
            state: Entity state with equipment slots
            modifiers: Ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            List of available attack actions
        """
        pass

    @abstractmethod
    def equip_item_to_slot(
        self,
        game_state: GameState,
        state: EntityState,
        item_index: str,
        slot_type: EquipmentSlotType | None = None,
        unequip: bool = False,
    ) -> EntityState:
        """Equip/unequip item.

        Args:
            game_state: Game state for pack-scoped repository access
            state: Current entity state
            item_index: Index of the item to equip/unequip
            slot_type: Target slot (auto-selects if None)
            unequip: True to remove from slots

        Returns:
            Updated EntityState with item equipped/unequipped

        Raises:
            ValueError: If item not found, not equippable, or constraints violated
        """
        pass


class ILevelProgressionService(ABC):
    """Interface for minimal character level-up progression."""

    @abstractmethod
    def level_up_character(self, game_state: GameState, character: CharacterInstance) -> None:
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
