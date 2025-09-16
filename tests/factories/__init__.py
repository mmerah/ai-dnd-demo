"""Shared factory helpers for backend unit tests."""

from .characters import make_character_instance, make_character_sheet
from .game_state import make_game_state
from .monsters import make_monster_instance, make_monster_sheet
from .npcs import make_npc_instance, make_npc_sheet
from .scenario import make_location, make_location_connection, make_quest, make_scenario

__all__ = [
    "make_character_sheet",
    "make_character_instance",
    "make_game_state",
    "make_monster_sheet",
    "make_monster_instance",
    "make_location",
    "make_location_connection",
    "make_quest",
    "make_scenario",
    "make_npc_sheet",
    "make_npc_instance",
]
