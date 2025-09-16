"""Factory helpers for character-related test data."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.models.attributes import Abilities
from app.models.character import CharacterSheet, Currency, Personality
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.item import InventoryItem
from app.models.spell import Spellcasting


def make_character_sheet(
    *,
    character_id: str = "hero",
    name: str = "Hero",
    race: str = "human",
    class_index: str = "fighter",
    starting_level: int = 1,
    abilities: Abilities | None = None,
    inventory: Iterable[InventoryItem] | None = None,
    spellcasting: Spellcasting | None = None,
    background: str = "soldier",
    alignment: str = "lawful-good",
    starting_experience_points: int = 0,
    starting_currency: Currency | None = None,
    personality: Personality | None = None,
    languages: Sequence[str] | None = None,
    starting_skill_indexes: Sequence[str] | None = None,
    content_packs: Sequence[str] | None = None,
) -> CharacterSheet:
    """Create a CharacterSheet with sensible defaults for tests."""
    abilities = abilities or Abilities(STR=12, DEX=10, CON=12, INT=8, WIS=10, CHA=10)
    starting_currency = starting_currency or Currency()
    personality = personality or Personality()
    languages = list(languages) if languages is not None else ["common"]
    starting_skill_indexes = list(starting_skill_indexes) if starting_skill_indexes is not None else []
    content_packs = list(content_packs) if content_packs is not None else ["srd"]
    return CharacterSheet(
        id=character_id,
        name=name,
        race=race,
        class_index=class_index,
        background=background,
        alignment=alignment,
        starting_level=starting_level,
        starting_experience_points=starting_experience_points,
        starting_abilities=abilities,
        starting_inventory=list(inventory) if inventory is not None else [],
        starting_currency=starting_currency,
        personality=personality,
        backstory="",
        languages=languages,
        starting_skill_indexes=starting_skill_indexes,
        starting_spellcasting=spellcasting,
        content_packs=content_packs,
    )


def make_character_instance(
    *,
    sheet: CharacterSheet | None = None,
    instance_id: str = "char-1",
    hp_current: int | None = None,
) -> CharacterInstance:
    """Create a CharacterInstance with a sensible default EntityState.

    Mirrors the pattern used in GameState factory but is reusable for tests
    that need a standalone instance.
    """
    sheet = sheet or make_character_sheet()
    hp = HitPoints(current=hp_current if hp_current is not None else 12, maximum=12, temporary=0)
    state = EntityState(
        abilities=sheet.starting_abilities,
        level=sheet.starting_level,
        experience_points=sheet.starting_experience_points,
        hit_points=hp,
        hit_dice=HitDice(total=1, current=1, type="d10"),
        currency=sheet.starting_currency.model_copy(),
        spellcasting=sheet.starting_spellcasting,
    )
    return CharacterInstance(
        instance_id=instance_id,
        template_id=sheet.id,
        sheet=sheet,
        state=state,
    )
