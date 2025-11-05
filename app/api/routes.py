"""Main API router that composes sub-routers."""

from fastapi import APIRouter

from .routers import (
    catalogs_router,
    characters_router,
    content_packs_router,
    game_router,
    scenarios_router,
    schemas_router,
)

router = APIRouter()

# Include sub-routers. Endpoints keep their full paths as defined.
router.include_router(game_router)
router.include_router(scenarios_router)
router.include_router(characters_router)
router.include_router(catalogs_router)
router.include_router(content_packs_router)
router.include_router(schemas_router)
