"""API endpoints for content pack management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_content_pack_registry
from app.api.schemas.content_packs import (
    ContentPackDetailResponse,
    ContentPackListResponse,
    ValidatePacksRequest,
    ValidatePacksResponse,
)
from app.interfaces.services.common import IContentPackRegistry

router = APIRouter(tags=["content-packs"])


@router.get("/content-packs", response_model=ContentPackListResponse)
async def list_content_packs(
    registry: Annotated[IContentPackRegistry, Depends(get_content_pack_registry)],
) -> ContentPackListResponse:
    """List all available content packs.

    Returns a list of content pack summaries including SRD and user packs.
    """
    packs = registry.list_packs()
    return ContentPackListResponse(packs=packs, total=len(packs))


@router.get("/content-packs/{pack_id}", response_model=ContentPackDetailResponse)
async def get_content_pack(
    pack_id: str, registry: Annotated[IContentPackRegistry, Depends(get_content_pack_registry)]
) -> ContentPackDetailResponse:
    """Get detailed information about a specific content pack.

    Args:
        pack_id: The ID of the content pack to retrieve

    Returns:
        Detailed content pack metadata

    Raises:
        404 if pack not found
    """
    pack = registry.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Content pack '{pack_id}' not found")

    return ContentPackDetailResponse(
        id=pack.id,
        name=pack.name,
        version=pack.version,
        author=pack.author,
        description=pack.description,
        pack_type=pack.pack_type,
        dependencies=pack.dependencies,
        created_at=pack.created_at,
        updated_at=pack.updated_at,
    )


@router.post("/content-packs/validate", response_model=ValidatePacksResponse)
async def validate_content_packs(
    request: ValidatePacksRequest, registry: Annotated[IContentPackRegistry, Depends(get_content_pack_registry)]
) -> ValidatePacksResponse:
    """Validate a set of content packs and their dependencies.

    Checks if all required dependencies are satisfied and returns
    the correct loading order for the packs.

    Args:
        request: List of pack IDs to validate

    Returns:
        Validation result with ordered pack list if valid
    """
    valid, error = registry.validate_dependencies(request.pack_ids)

    ordered_packs = []
    if valid:
        try:
            ordered_packs = registry.get_pack_order(request.pack_ids)
        except ValueError as e:
            valid = False
            error = str(e)

    return ValidatePacksResponse(valid=valid, error=error, ordered_packs=ordered_packs)
