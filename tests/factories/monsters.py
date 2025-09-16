"""Factory helpers for monster test data."""

from __future__ import annotations

from app.models.attributes import Abilities
from app.models.instances.entity_state import HitPoints
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
