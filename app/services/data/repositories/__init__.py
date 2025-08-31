"""Repository implementations for data access."""

from app.services.data.repositories.base_repository import BaseRepository
from app.services.data.repositories.item_repository import ItemRepository
from app.services.data.repositories.monster_repository import MonsterRepository
from app.services.data.repositories.spell_repository import SpellRepository

__all__ = [
    "BaseRepository",
    "ItemRepository",
    "MonsterRepository",
    "SpellRepository",
]
