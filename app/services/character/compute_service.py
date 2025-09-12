"""Character compute service implementation using repository interfaces."""

from __future__ import annotations

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.data import IItemRepository, IRepository, ISpellRepository
from app.models.attributes import Abilities, AbilityModifiers, AttackAction, SavingThrows, SkillValue
from app.models.character import CharacterSheet
from app.models.class_definitions import ClassDefinition
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.item import InventoryItem, ItemDefinition, ItemSubtype, ItemType
from app.models.race import RaceDefinition
from app.models.skill import Skill
from app.utils.ability_utils import ALL_ABILITY_CODES, get_ability_modifier, normalize_ability_name, set_ability_value

logger = logging.getLogger(__name__)


class CharacterComputeService(ICharacterComputeService):
    """Computes derived character values from core inputs.

    Intended to consume state from EntityState (abilities, level) and
    class_index from the template (CharacterInstance.sheet.class_index),
    returning derived values used across both CharacterInstance and NPCInstance.
    """

    def __init__(
        self,
        class_repository: IRepository[ClassDefinition],
        skill_repository: IRepository[Skill],
        item_repository: IItemRepository,
        spell_repository: ISpellRepository,
        race_repository: IRepository[RaceDefinition],
    ) -> None:
        self.class_repository = class_repository
        self.skill_repository = skill_repository
        self.item_repository = item_repository
        self.spell_repository = spell_repository
        self.race_repository = race_repository

    # Interface implementation
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
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> SavingThrows:
        out = SavingThrows()
        cls_def = self.class_repository.get(class_index)
        proficient = set(cls_def.saving_throws)
        for ability_code in ALL_ABILITY_CODES:
            base = get_ability_modifier(modifiers, ability_code)
            value = base + (
                proficiency_bonus if ability_code.lower() in proficient or ability_code in proficient else 0
            )
            set_ability_value(out, ability_code, value)
        return out

    def _skill_base_mod(self, skill_index: str, modifiers: AbilityModifiers) -> int:
        skill = self.skill_repository.get(skill_index)
        ability_code = normalize_ability_name(skill.ability)
        return get_ability_modifier(modifiers, ability_code) if ability_code else 0

    def compute_skills(
        self,
        class_index: str,
        selected_skills: list[str],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[SkillValue]:
        out: list[SkillValue] = []
        # If no explicit selection, pick first allowed skills from class proficiency choices
        chosen: list[str] = list(selected_skills)
        if not chosen:
            cls_def = self.class_repository.get(class_index)
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
                    valid = [opt for opt in options if self.skill_repository.validate_reference(opt)]
                    for sk in valid:
                        if len(chosen) >= to_choose:
                            break
                        if sk not in chosen:
                            chosen.append(sk)

        selected = set(chosen)
        for key in self.skill_repository.list_keys():
            base = self._skill_base_mod(key, modifiers)
            value = base + (proficiency_bonus if key in selected else 0)
            out.append(SkillValue(index=key, value=value))
        return out

    def compute_armor_class(self, modifiers: AbilityModifiers, inventory: list[InventoryItem]) -> int:
        # Minimal equipment handling: pick best equipped armor; add one shield if equipped
        base_unarmored = 10 + modifiers.DEX
        # Item repository is always provided in the constructor

        equipped_defs: list[tuple[InventoryItem, ItemDefinition]] = []
        for it in inventory:
            if (it.equipped_quantity or 0) <= 0:
                continue
            try:
                item_def = self.item_repository.get(it.name)
                equipped_defs.append((it, item_def))
            except RepositoryNotFoundError:
                logger.warning(f"Can't compute new armor class as {it.name} not found in ItemRepository")
                continue

        # Separate shields and body armor
        best_body_ac: int | None = None
        best_body_item = None
        shield_bonus = 0
        for _inv, idef in equipped_defs:
            if idef.type != ItemType.ARMOR:
                continue
            if idef.subtype == ItemSubtype.SHIELD and idef.armor_class:
                # Only one shield applies; use the max if multiple
                shield_bonus = max(shield_bonus, idef.armor_class)
            elif (
                idef.subtype in (ItemSubtype.LIGHT, ItemSubtype.MEDIUM, ItemSubtype.HEAVY)
                and idef.armor_class is not None
                and (best_body_ac is None or idef.armor_class > best_body_ac)
            ):
                best_body_ac = idef.armor_class
                best_body_item = idef

        if best_body_item is None:
            return base_unarmored + shield_bonus

        # Compute armor AC with Dex rules
        ac = best_body_ac or 10
        if best_body_item.dex_bonus:
            if best_body_item.subtype == ItemSubtype.MEDIUM:
                ac += min(2, max(0, modifiers.DEX))
            else:  # LIGHT
                ac += modifiers.DEX
        # HEAVY ignores Dex

        return ac + shield_bonus

    def compute_initiative_bonus(self, modifiers: AbilityModifiers) -> int:
        return modifiers.DEX

    def compute_spell_numbers(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        try:
            cls_def = self.class_repository.get(class_index)
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

    def compute_hit_points_and_dice(self, class_index: str, level: int, con_modifier: int) -> tuple[int, int, str]:
        try:
            cls_def = self.class_repository.get(class_index)
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

    def compute_speed(self, race_index: str, inventory: list[InventoryItem]) -> int:
        # Minimal rule: base speed from race; ignore armor penalties
        try:
            race = self.race_repository.get(race_index)
            return race.speed
        except RepositoryNotFoundError:
            return 30

    def initialize_entity_state(self, sheet: CharacterSheet) -> EntityState:
        abilities = sheet.starting_abilities
        level = sheet.starting_level

        # Derived basics
        modifiers = self.compute_ability_modifiers(abilities)
        proficiency = self.compute_proficiency_bonus(level)
        saving_throws = self.compute_saving_throws(sheet.class_index, modifiers, proficiency)
        skills = self.compute_skills(
            sheet.class_index,
            selected_skills=sheet.starting_skill_indexes,
            modifiers=modifiers,
            proficiency_bonus=proficiency,
        )
        armor_class = self.compute_armor_class(modifiers, sheet.starting_inventory)
        initiative_bonus = self.compute_initiative_bonus(modifiers)

        # HP / Hit Dice
        max_hp, hit_dice_total, hit_die_type = self.compute_hit_points_and_dice(sheet.class_index, level, modifiers.CON)

        # Spellcasting copy with computed numbers
        spellcasting = None
        if sheet.starting_spellcasting is not None:
            sc = sheet.starting_spellcasting.model_copy(deep=True)
            dc, atk = self.compute_spell_numbers(sheet.class_index, modifiers, proficiency)
            sc.spell_save_dc = dc
            sc.spell_attack_bonus = atk
            spellcasting = sc

        # Speed from race (minimal rule)
        speed = self.compute_speed(sheet.race, sheet.starting_inventory)

        attacks = self.compute_attacks(
            sheet.class_index,
            sheet.race,
            sheet.starting_inventory,
            modifiers,
            proficiency,
        )

        return EntityState(
            abilities=abilities,
            level=level,
            experience_points=sheet.starting_experience_points,
            hit_points=HitPoints(current=max_hp, maximum=max_hp, temporary=0),
            hit_dice=HitDice(total=hit_dice_total, current=hit_dice_total, type=hit_die_type),
            armor_class=armor_class,
            initiative_bonus=initiative_bonus,
            speed=speed,
            saving_throws=saving_throws,
            skills=skills,
            attacks=attacks,
            conditions=[],
            exhaustion_level=0,
            inspiration=False,
            inventory=sheet.starting_inventory,
            currency=sheet.starting_currency,
            spellcasting=spellcasting,
        )

    def recompute_entity_state(self, sheet: CharacterSheet, state: EntityState) -> EntityState:
        # Compute all derived fields based on current state + sheet
        modifiers = self.compute_ability_modifiers(state.abilities)
        proficiency = self.compute_proficiency_bonus(state.level)
        saving_throws = self.compute_saving_throws(sheet.class_index, modifiers, proficiency)

        # Selected skills from sheet if present
        selected_skills = sheet.starting_skill_indexes
        skills = self.compute_skills(sheet.class_index, selected_skills, modifiers, proficiency)

        armor_class = self.compute_armor_class(modifiers, state.inventory)
        initiative_bonus = self.compute_initiative_bonus(modifiers)
        speed = self.compute_speed(sheet.race, state.inventory)

        # HP and Hit Dice totals/types based on class and level
        max_hp, hd_total, hd_type = self.compute_hit_points_and_dice(sheet.class_index, state.level, modifiers.CON)
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
            dc, atk = self.compute_spell_numbers(sheet.class_index, modifiers, proficiency)
            new_state.spellcasting.spell_save_dc = dc
            new_state.spellcasting.spell_attack_bonus = atk

        # Rebuild attacks from equipped items
        new_state.attacks = self.compute_attacks(
            sheet.class_index,
            sheet.race,
            new_state.inventory,
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

    def _is_proficient_with_weapon(self, class_index: str, race_index: str, idef: ItemDefinition) -> bool:
        try:
            cls_def = self.class_repository.get(class_index)
            profs = set(cls_def.proficiencies or [])
        except RepositoryNotFoundError:
            profs = set()

        try:
            race_def = self.race_repository.get(race_index)
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
        class_index: str,
        race_index: str,
        inventory: list[InventoryItem],
        modifiers: AbilityModifiers,
        proficiency_bonus: int,
    ) -> list[AttackAction]:
        attacks: list[AttackAction] = []
        # Build from equipped weapons
        for inv in inventory:
            if (inv.equipped_quantity or 0) <= 0:
                continue
            try:
                idef = self.item_repository.get(inv.name)
            except RepositoryNotFoundError:
                logger.warning(f"Can't compute attacks as {inv.name} not found in ItemRepository")
                continue
            if idef.type != ItemType.WEAPON:
                continue

            ability_mod = self._choose_attack_mod(idef, modifiers)
            prof = self._is_proficient_with_weapon(class_index, race_index, idef)
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

    def _is_shield(self, idef: ItemDefinition) -> bool:
        return idef.type == ItemType.ARMOR and idef.subtype == ItemSubtype.SHIELD

    def _is_body_armor(self, idef: ItemDefinition) -> bool:
        return idef.type == ItemType.ARMOR and idef.subtype in (
            ItemSubtype.LIGHT,
            ItemSubtype.MEDIUM,
            ItemSubtype.HEAVY,
        )

    def _enforce_equip_constraints(self, inventory: list[InventoryItem], equipping_def: ItemDefinition) -> None:
        """
        Enforce simple equipment constraints.

        - Only one shield may be equipped
        - Only one body armor (light/medium/heavy) may be equipped
        """
        if self._is_shield(equipping_def):
            for it in inventory:
                if (it.equipped_quantity or 0) <= 0:
                    continue
                current_def = self.item_repository.get(it.name)
                if self._is_shield(current_def):
                    raise ValueError("Cannot equip more than one shield at a time")
        elif self._is_body_armor(equipping_def):
            for it in inventory:
                if (it.equipped_quantity or 0) <= 0:
                    continue
                current_def = self.item_repository.get(it.name)
                if self._is_body_armor(current_def):
                    raise ValueError("Already wearing body armor; unequip it first")

    def set_item_equipped(self, state: EntityState, item_name: str, equipped: bool) -> EntityState:
        inventory = state.inventory
        # Locate item by name (case-insensitive fallback)
        item = next((it for it in inventory if it.name == item_name), None)
        if not item:
            item = next((it for it in inventory if it.name.lower() == item_name.lower()), None)
        if not item:
            raise ValueError(f"Item '{item_name}' not found in inventory")

        # Validate using item repository
        try:
            item_def = self.item_repository.get(item.name)
        except RepositoryNotFoundError as e:
            raise ValueError(f"Unknown item definition for '{item.name}'") from e
        if item_def.type not in (ItemType.WEAPON, ItemType.ARMOR):
            raise ValueError(f"Item '{item.name}' is not equippable")

        # Single-entry model: adjust equipped_quantity by one
        if equipped:
            # TODO(MVP2): move to a slot-based equipment system (typed slots, constraints)
            self._enforce_equip_constraints(inventory, item_def)
            if item.equipped_quantity < item.quantity:
                item.equipped_quantity += 1
        else:
            if item.equipped_quantity > 0:
                item.equipped_quantity -= 1

        # Return updated state
        return state
