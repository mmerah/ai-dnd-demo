from fastapi import APIRouter

from .catalogs import router as catalogs_router
from .characters import router as characters_router
from .game import router as game_router
from .scenarios import router as scenarios_router

__all__ = [
    "APIRouter",
    "game_router",
    "scenarios_router",
    "characters_router",
    "catalogs_router",
]
