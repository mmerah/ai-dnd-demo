"""Factory helpers for monster test data."""

from __future__ import annotations

from app.models.attributes import Abilities
from app.models.character import Currency
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.instances.monster_instance import MonsterInstance
from app.models.monster import MonsterSheet


def make_monster_sheet(
    *,
    name: str = "Wolf",
    index: str | None = None,
    armor_class: int = 12,
    hit_points: int = 8,
) -> MonsterSheet:
    """Create a minimal MonsterSheet for spawning."""
    index = index or name.lower().replace(" ", "-")
    return MonsterSheet(
        index=index,
        name=name,
        type="beast",
        size="Medium",
        alignment="unaligned",
        armor_class=armor_class,
        hit_points=HitPoints(current=hit_points, maximum=hit_points, temporary=0),
        hit_dice="2d8",
        speed="30 ft.",
        challenge_rating=0.25,
        abilities=Abilities(STR=12, DEX=12, CON=12, INT=3, WIS=10, CHA=6),
        senses="darkvision 60 ft.",
        attacks=[],
        languages=[],
        content_pack="srd",
    )


def make_monster_instance(
    *,
    sheet: MonsterSheet | None = None,
    instance_id: str = "monster-1",
    current_location_id: str = "start",
    hp_current: int | None = None,
) -> MonsterInstance:
    """Create a MonsterInstance from a sheet with sensible defaults."""
    sheet = sheet or make_monster_sheet()
    hp = HitPoints(
        current=hp_current if hp_current is not None else sheet.hit_points.current,
        maximum=sheet.hit_points.maximum,
        temporary=sheet.hit_points.temporary,
    )
    state = EntityState(
        abilities=sheet.abilities,
        level=1,
        experience_points=0,
        hit_points=hp,
        hit_dice=HitDice(total=1, current=1, type="d8"),
        currency=Currency(),
    )
    return MonsterInstance(
        instance_id=instance_id,
        template_id=sheet.index,
        sheet=sheet,
        state=state,
        current_location_id=current_location_id,
    )
