"""Character compute service implementation using repository interfaces."""

from __future__ import annotations

from app.interfaces.services import ICharacterComputeService, IItemRepository, IRepository, ISpellRepository
from app.models.ability import Abilities, AbilityModifiers, SavingThrows
from app.models.class_definitions import ClassDefinition
from app.models.instances.entity_state import EntitySkill
from app.models.skill import Skill


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
        item_repository: IItemRepository | None = None,
        spell_repository: ISpellRepository | None = None,
    ) -> None:
        self.class_repository = class_repository
        self.skill_repository = skill_repository
        self.item_repository = item_repository
        self.spell_repository = spell_repository

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
        proficient = set(cls_def.saving_throws or []) if cls_def else set()
        for ability in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
            base = getattr(modifiers, ability)
            value = base + (proficiency_bonus if ability.lower() in proficient or ability in proficient else 0)
            setattr(out, ability, value)
        return out

    def _skill_base_mod(self, skill_index: str, modifiers: AbilityModifiers) -> int:
        skill = self.skill_repository.get(skill_index)
        if not skill:
            return 0
        ability_map = {
            "strength": "STR",
            "dexterity": "DEX",
            "constitution": "CON",
            "intelligence": "INT",
            "wisdom": "WIS",
            "charisma": "CHA",
        }
        key = ability_map.get(skill.ability.lower())
        return getattr(modifiers, key) if key else 0

    def compute_skills(
        self, selected_skills: list[str], modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> list[EntitySkill]:
        out: list[EntitySkill] = []
        for key in self.skill_repository.list_keys():
            base = self._skill_base_mod(key, modifiers)
            value = base + (proficiency_bonus if key in selected_skills else 0)
            out.append(EntitySkill(index=key, value=value))
        return out

    def compute_armor_class(self, modifiers: AbilityModifiers) -> int:
        # Placeholder basic unarmored AC until equipment logic is added
        return 10 + modifiers.DEX

    def compute_initiative(self, modifiers: AbilityModifiers) -> int:
        return modifiers.DEX

    def compute_spell_numbers(
        self, class_index: str, modifiers: AbilityModifiers, proficiency_bonus: int
    ) -> tuple[int | None, int | None]:
        cls_def = self.class_repository.get(class_index)
        if not cls_def or not cls_def.spellcasting_ability:
            return None, None
        ability_map = {
            "strength": "STR",
            "dexterity": "DEX",
            "constitution": "CON",
            "intelligence": "INT",
            "wisdom": "WIS",
            "charisma": "CHA",
        }
        key = ability_map.get(cls_def.spellcasting_ability.lower())
        if not key:
            return None, None
        ability_mod = getattr(modifiers, key)
        dc = 8 + proficiency_bonus + ability_mod
        atk = proficiency_bonus + ability_mod
        return dc, atk
