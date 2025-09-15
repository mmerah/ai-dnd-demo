"""Character compute service implementation using repository interfaces."""

from __future__ import annotations

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.data import IRepositoryProvider
from app.models.attributes import Abilities, AbilityModifiers, AttackAction, SavingThrows, SkillValue
from app.models.character import CharacterSheet
from app.models.equipment_slots import EquipmentSlotType
from app.models.game_state import GameState
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.item import InventoryItem, ItemDefinition, ItemSubtype, ItemType
from app.utils.ability_utils import ALL_ABILITY_CODES, get_ability_modifier, normalize_ability_name, set_ability_value

logger = logging.getLogger(__name__)


class CharacterComputeService(ICharacterComputeService):
    """Computes derived character values from core inputs. Stateless service."""

    def __init__(self, repository_provider: IRepositoryProvider) -> None:
        """Initialize with a repository provider.

        Args:
            repository_provider: Provider for pack-scoped repositories
        """
        self.repository_provider = repository_provider

    def compute_ability_modifiers(self, abilities: Abilities) -> AbilityModifiers:
        def mod(score: int) -> int:
            return (score - 10) // 2

        return AbilityModifiers(
            STR=mod(abilities.STR),
            DEX=mod(abilities.DEX),
            CON=mod(abilities.CON),
            INT=mod(abilities.INT),
            WIS=mod(abilities.WIS),
            CHA=mod(abilities.CHA),
        )

    def compute_proficiency_bonus(self, level: int) -> int:
        if level <= 4:
            return 2
        if level <= 8:
            return 3
        if level <= 12:
            return 4
        if level <= 16:
            return 5
        return 6

    def compute_saving_throws(
        self, game_state: GameState, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> SavingThrows:
        out = SavingThrows()
        cls_def = self.repository_provider.get_class_repository_for(game_state).get(class_index)
        proficient = set(cls_def.saving_throws)
        for ability_code in ALL_ABILITY_CODES:
            base = get_ability_modifier(modifiers, ability_code)
            value = base + (
                proficiency_bonus if ability_code.lower() in proficient or ability_code in proficient else 0
            )
            set_ability_value(out, ability_code, value)
        return out

    def _skill_base_mod(self, game_state: GameState, skill_index: str, modifiers: AbilityModifiers) -> int:
        skill = self.repository_provider.get_skill_repository_for(game_state).get(skill_index)
        ability_code = normalize_ability_name(skill.ability)
        return get_ability_modifier(modifiers, ability_code) if ability_code else 0

    def compute_skills(
        self,
        game_state: GameState,
        class_index: str,
        selected_skills: list[str],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[SkillValue]:
        out: list[SkillValue] = []
        # If no explicit selection, pick first allowed skills from class proficiency choices
        chosen: list[str] = list(selected_skills)
        skill_repo = self.repository_provider.get_skill_repository_for(game_state)
        if not chosen:
            cls_def = self.repository_provider.get_class_repository_for(game_state).get(class_index)
            if cls_def.proficiency_choices:
                for choice in cls_def.proficiency_choices:
                    to_choose = int(choice.choose)
                    # Filter to skill-* entries and strip prefix
                    options = [
                        opt[len("skill-") :]
                        for opt in choice.from_options
                        if isinstance(opt, str) and opt.startswith("skill-")
                    ]
                    # Deterministic selection: first N valid skills
                    valid = [opt for opt in options if skill_repo.validate_reference(opt)]
                    for sk in valid:
                        if len(chosen) >= to_choose:
                            break
                        if sk not in chosen:
                            chosen.append(sk)

        selected = set(chosen)
        for key in skill_repo.list_keys():
            base = self._skill_base_mod(game_state, key, modifiers)
            value = base + (proficiency_bonus if key in selected else 0)
            out.append(SkillValue(index=key, value=value))
        return out

    def compute_armor_class(self, game_state: GameState, modifiers: AbilityModifiers, state: EntityState) -> int:
        base_ac = 10 + modifiers.DEX
        item_repo = self.repository_provider.get_item_repository_for(game_state)

        # Check chest slot for armor
        chest_item = state.equipment_slots.chest
        if chest_item:
            try:
                armor_def = item_repo.get(chest_item)
                if armor_def.armor_class:
                    base_ac = armor_def.armor_class
                    if armor_def.subtype == ItemSubtype.MEDIUM:
                        base_ac += min(2, modifiers.DEX)
                    elif armor_def.subtype == ItemSubtype.LIGHT:
                        base_ac += modifiers.DEX
                    # Heavy armor ignores DEX
            except RepositoryNotFoundError:
                logger.warning(f"Armor item '{chest_item}' not found in repository")
                pass

        # Check for shields
        shield_bonus = 0
        for slot in [EquipmentSlotType.MAIN_HAND, EquipmentSlotType.OFF_HAND]:
            item_index = state.equipment_slots.get_slot(slot)
            if item_index:
                try:
                    item_def = item_repo.get(item_index)
                    if item_def.subtype == ItemSubtype.SHIELD and item_def.armor_class:
                        shield_bonus = max(shield_bonus, item_def.armor_class)
                except RepositoryNotFoundError:
                    logger.warning(f"Shield item '{item_index}' not found in repository")
                    pass

        return base_ac + shield_bonus

    def compute_initiative_bonus(self, modifiers: AbilityModifiers) -> int:
        return modifiers.DEX

    def compute_spell_numbers(
        self, game_state: GameState, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        try:
            cls_def = self.repository_provider.get_class_repository_for(game_state).get(class_index)
        except RepositoryNotFoundError:
            return None, None
        if not cls_def.spellcasting_ability:
            return None, None
        ability_code = normalize_ability_name(cls_def.spellcasting_ability)
        if not ability_code:
            return None, None
        ability_mod = get_ability_modifier(modifiers, ability_code)
        dc = 8 + proficiency_bonus + ability_mod
        atk = proficiency_bonus + ability_mod
        return dc, atk

    def compute_hit_points_and_dice(
        self, game_state: GameState, class_index: str, level: int, con_modifier: int
    ) -> tuple[int, int, str]:
        try:
            cls_def = self.repository_provider.get_class_repository_for(game_state).get(class_index)
            hit_die = cls_def.hit_die if cls_def.hit_die else 8
        except RepositoryNotFoundError:
            hit_die = 8
        # Level 1
        max_hp = max(1, hit_die + con_modifier)
        # Levels 2..N use average + CON mod, at least 1 per level
        if level > 1:
            avg = (hit_die // 2) + 1
            per_level = max(1, avg + con_modifier)
            max_hp += (level - 1) * per_level
        hit_dice_total = level
        return max_hp, hit_dice_total, f"d{hit_die}"

    def compute_speed(self, game_state: GameState, race_index: str, inventory: list[InventoryItem]) -> int:
        # Minimal rule: base speed from race; ignore armor penalties
        try:
            race = self.repository_provider.get_race_repository_for(game_state).get(race_index)
            return race.speed
        except RepositoryNotFoundError:
            return 30

    def initialize_entity_state(self, game_state: GameState, sheet: CharacterSheet) -> EntityState:
        abilities = sheet.starting_abilities
        level = sheet.starting_level

        # Derived basics
        modifiers = self.compute_ability_modifiers(abilities)
        proficiency = self.compute_proficiency_bonus(level)
        saving_throws = self.compute_saving_throws(game_state, sheet.class_index, modifiers, proficiency)
        skills = self.compute_skills(
            game_state,
            sheet.class_index,
            selected_skills=sheet.starting_skill_indexes,
            modifiers=modifiers,
            proficiency_bonus=proficiency,
        )
        initiative_bonus = self.compute_initiative_bonus(modifiers)
        speed = self.compute_speed(game_state, sheet.race, sheet.starting_inventory)
        max_hp, hit_dice_total, hit_die_type = self.compute_hit_points_and_dice(
            game_state, sheet.class_index, level, modifiers.CON
        )
        spellcasting = None
        if sheet.starting_spellcasting is not None:
            sc = sheet.starting_spellcasting.model_copy(deep=True)
            dc, atk = self.compute_spell_numbers(game_state, sheet.class_index, modifiers, proficiency)
            sc.spell_save_dc = dc
            sc.spell_attack_bonus = atk
            spellcasting = sc

        # Create state with all computed values. AC and attacks will be computed after auto-equip
        state = EntityState(
            abilities=abilities,
            level=level,
            experience_points=sheet.starting_experience_points,
            hit_points=HitPoints(current=max_hp, maximum=max_hp, temporary=0),
            hit_dice=HitDice(total=hit_dice_total, current=hit_dice_total, type=hit_die_type),
            armor_class=10,
            initiative_bonus=initiative_bonus,
            speed=speed,
            saving_throws=saving_throws,
            skills=skills,
            attacks=[],
            conditions=[],
            exhaustion_level=0,
            inspiration=False,
            inventory=sheet.starting_inventory,
            currency=sheet.starting_currency,
            spellcasting=spellcasting,
        )

        # Auto-equip initial items if equipment slots are empty
        self._auto_equip_initial_items(game_state, state)

        # Compute AC and attacks after auto-equipping items
        state.armor_class = self.compute_armor_class(game_state, modifiers, state)
        state.attacks = self.compute_attacks(
            game_state,
            sheet.class_index,
            sheet.race,
            state,
            modifiers,
            proficiency,
        )

        return state

    def recompute_entity_state(self, game_state: GameState, sheet: CharacterSheet, state: EntityState) -> EntityState:
        # Compute all derived fields based on current state + sheet
        modifiers = self.compute_ability_modifiers(state.abilities)
        proficiency = self.compute_proficiency_bonus(state.level)
        saving_throws = self.compute_saving_throws(game_state, sheet.class_index, modifiers, proficiency)

        # Selected skills from sheet if present
        selected_skills = sheet.starting_skill_indexes
        skills = self.compute_skills(game_state, sheet.class_index, selected_skills, modifiers, proficiency)

        armor_class = self.compute_armor_class(game_state, modifiers, state)
        initiative_bonus = self.compute_initiative_bonus(modifiers)
        speed = self.compute_speed(game_state, sheet.race, state.inventory)

        # HP and Hit Dice totals/types based on class and level
        max_hp, hd_total, hd_type = self.compute_hit_points_and_dice(
            game_state, sheet.class_index, state.level, modifiers.CON
        )
        current_hp = min(state.hit_points.current, max_hp)
        current_hd = min(state.hit_dice.current or hd_total, hd_total)

        new_state = state.model_copy(deep=True)
        new_state.saving_throws = saving_throws
        new_state.skills = skills
        new_state.armor_class = armor_class
        new_state.initiative_bonus = initiative_bonus
        new_state.speed = speed
        new_state.hit_points.maximum = max_hp
        new_state.hit_points.current = current_hp
        new_state.hit_dice.total = hd_total
        new_state.hit_dice.current = current_hd
        new_state.hit_dice.type = hd_type

        if new_state.spellcasting is not None:
            dc, atk = self.compute_spell_numbers(game_state, sheet.class_index, modifiers, proficiency)
            new_state.spellcasting.spell_save_dc = dc
            new_state.spellcasting.spell_attack_bonus = atk

        # Rebuild attacks from equipped items
        new_state.attacks = self.compute_attacks(
            game_state,
            sheet.class_index,
            sheet.race,
            new_state,
            modifiers,
            proficiency,
        )

        return new_state

    def _choose_attack_mod(self, idef: ItemDefinition, modifiers: AbilityModifiers) -> int:
        # Finesse: choose the higher of STR/DEX
        if idef.subtype == ItemSubtype.RANGED or "Ammunition" in (idef.properties or []):
            return modifiers.DEX
        if "Finesse" in (idef.properties or []):
            return modifiers.DEX if modifiers.DEX >= modifiers.STR else modifiers.STR
        # Thrown uses STR by default
        return modifiers.STR

    def _text_index_from_name(self, name: str) -> str:
        # Normalize name to a simple index-like token (best-effort)
        return name.lower().replace(",", "").replace(" ", "-")

    def _is_proficient_with_weapon(
        self, game_state: GameState, class_index: str, race_index: str, idef: ItemDefinition
    ) -> bool:
        try:
            cls_def = self.repository_provider.get_class_repository_for(game_state).get(class_index)
            profs = set(cls_def.proficiencies or [])
        except RepositoryNotFoundError:
            profs = set()

        try:
            race_def = self.repository_provider.get_race_repository_for(game_state).get(race_index)
            race_profs = set(race_def.weapon_proficiencies or []) if race_def.weapon_proficiencies else set()
        except RepositoryNotFoundError:
            race_profs = set()
        all_profs = profs | race_profs
        if "simple-weapons" in all_profs or "martial-weapons" in all_profs:
            return True
        # Specific weapons (e.g., longswords, hand-crossbows)
        weapon_idx = self._text_index_from_name(idef.name)
        return any(weapon_idx in p for p in all_profs)

    def _format_damage_with_mod(self, base_damage: str, mod: int) -> str:
        if mod == 0:
            return base_damage
        sign = "+" if mod > 0 else "-"
        return f"{base_damage}{sign}{abs(mod)}"

    def _determine_attack_range(self, idef: ItemDefinition) -> str:
        """Determine attack range from weapon subtype."""
        if not idef.subtype:
            logger.warning(f"Weapon '{idef.name}' has no subtype, defaulting to melee range")
            return "melee"

        if idef.subtype == ItemSubtype.RANGED:
            return "ranged"
        elif idef.subtype == ItemSubtype.MELEE:
            return "melee"
        else:
            logger.warning(f"Weapon '{idef.name}' has unexpected subtype '{idef.subtype}', defaulting to melee range")
            return "melee"

    def compute_attacks(
        self,
        game_state: GameState,
        class_index: str,
        race_index: str,
        state: EntityState,
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[AttackAction]:
        attacks: list[AttackAction] = []
        item_repo = self.repository_provider.get_item_repository_for(game_state)

        # Build from equipped weapons in hand slots
        for slot in [EquipmentSlotType.MAIN_HAND, EquipmentSlotType.OFF_HAND]:
            item_index = state.equipment_slots.get_slot(slot)
            if not item_index:
                continue
            try:
                idef = item_repo.get(item_index)
            except RepositoryNotFoundError:
                logger.warning(f"Can't compute attacks as {item_index} not found in ItemRepository")
                continue
            if idef.type != ItemType.WEAPON:
                continue

            ability_mod = self._choose_attack_mod(idef, modifiers)
            prof = self._is_proficient_with_weapon(game_state, class_index, race_index, idef)
            attack_roll_bonus = ability_mod + (proficiency_bonus if prof else 0)
            dmg = self._format_damage_with_mod(idef.damage, ability_mod)
            attack_range = self._determine_attack_range(idef)
            attacks.append(
                AttackAction(
                    name=idef.name,
                    attack_roll_bonus=attack_roll_bonus,
                    damage=dmg,
                    damage_type=idef.damage_type,
                    range=attack_range,
                    properties=list(idef.properties or []),
                )
            )

        # Fallback: unarmed strike
        if not attacks:
            str_mod = modifiers.STR
            attack_roll_bonus = str_mod + proficiency_bonus
            base = "1"
            dmg = self._format_damage_with_mod(base, str_mod)
            attacks.append(
                AttackAction(
                    name="Unarmed Strike",
                    attack_roll_bonus=attack_roll_bonus,
                    damage=dmg,
                    damage_type="bludgeoning",
                    range="melee",
                )
            )

        return attacks

    def equip_item_to_slot(
        self,
        game_state: GameState,
        state: EntityState,
        item_index: str,
        slot_type: EquipmentSlotType | None = None,
        unequip: bool = False,
    ) -> EntityState:
        # Validate item exists in inventory
        item = next((it for it in state.inventory if it.index == item_index), None)
        if not item:
            raise ValueError(f"Item '{item_index}' not found in inventory")

        # Get item definition
        item_repo = self.repository_provider.get_item_repository_for(game_state)
        try:
            item_def = item_repo.get(item_index)
        except RepositoryNotFoundError as e:
            logger.warning(f"Item definition for '{item_index}' not found in repository")
            raise ValueError(f"Unknown item definition: '{item_index}'") from e

        if unequip:
            cleared = state.equipment_slots.clear_item(item_index)
            if not cleared:
                raise ValueError(f"Item '{item_index}' is not equipped")
            return state

        # Validate item is equippable
        valid_slots = item_def.get_valid_slots()
        if not valid_slots:
            raise ValueError(f"Item '{item_def.name}' cannot be equipped")

        # Auto-select slot if not specified
        if slot_type is None:
            # Pick first valid empty slot, or first valid slot
            for slot in valid_slots:
                if state.equipment_slots.get_slot(slot) is None:
                    slot_type = slot
                    break
            if slot_type is None:
                slot_type = valid_slots[0]

        # Validate requested slot
        if slot_type not in valid_slots:
            raise ValueError(f"Item '{item_def.name}' cannot be equipped in {slot_type}")

        # Check quantity available
        equipped_count = len(state.equipment_slots.find_item_slots(item_index))
        if equipped_count >= item.quantity:
            raise ValueError(f"All {item.quantity} '{item_def.name}' are already equipped")

        # Handle two-handed weapons
        if item_def.is_two_handed and slot_type == EquipmentSlotType.MAIN_HAND and state.equipment_slots.off_hand:
            raise ValueError("Cannot equip two-handed weapon: off-hand slot occupied")

        # Clear current item in slot if any
        current = state.equipment_slots.get_slot(slot_type)
        if current:
            logger.warning(f"Replacing '{current}' in slot {slot_type} with '{item_index}'")
            state.equipment_slots.set_slot(slot_type, None)

        # Equip the item
        state.equipment_slots.set_slot(slot_type, item_index)

        # Block off-hand for two-handed weapons
        if item_def.is_two_handed and slot_type == EquipmentSlotType.MAIN_HAND:
            state.equipment_slots.off_hand = None

        return state

    def _auto_equip_initial_items(self, game_state: GameState, state: EntityState) -> None:
        """Auto-equip items on initial load (replaces equipped_quantity)."""
        item_repo = self.repository_provider.get_item_repository_for(game_state)

        # Priority order for auto-equipping
        for item in state.inventory:
            if state.equipment_slots.chest is None:
                # Try to equip armor
                try:
                    item_def = item_repo.get(item.index)
                    if item_def.type == ItemType.ARMOR and item_def.subtype in (
                        ItemSubtype.LIGHT,
                        ItemSubtype.MEDIUM,
                        ItemSubtype.HEAVY,
                    ):
                        state.equipment_slots.chest = item.index
                        continue
                except RepositoryNotFoundError:
                    pass

            if state.equipment_slots.main_hand is None:
                # Try to equip primary weapon
                try:
                    item_def = item_repo.get(item.index)
                    if item_def.type == ItemType.WEAPON:
                        state.equipment_slots.main_hand = item.index
                        if item_def.is_two_handed:
                            # Block off-hand
                            state.equipment_slots.off_hand = None
                        continue
                except RepositoryNotFoundError:
                    pass

            if state.equipment_slots.off_hand is None and state.equipment_slots.main_hand:
                # Try to equip shield or secondary weapon
                try:
                    item_def = item_repo.get(item.index)
                    main_def = item_repo.get(state.equipment_slots.main_hand)
                    if (
                        not main_def.is_two_handed
                        and item_def.subtype == ItemSubtype.SHIELD
                        or (item_def.type == ItemType.WEAPON and item.index != state.equipment_slots.main_hand)
                    ):
                        state.equipment_slots.off_hand = item.index
                        continue
                except RepositoryNotFoundError:
                    pass

            if state.equipment_slots.ammunition is None:
                # Try to equip ammunition
                try:
                    item_def = item_repo.get(item.index)
                    if item_def.type == ItemType.AMMUNITION:
                        state.equipment_slots.ammunition = item.index
                except RepositoryNotFoundError:
                    pass
