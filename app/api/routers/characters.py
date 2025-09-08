"""Character catalog endpoints."""

from fastapi import APIRouter, HTTPException

from app.container import container
from app.models.character import CharacterSheet

router = APIRouter()


@router.get("/characters", response_model=list[CharacterSheet])
async def list_available_characters() -> list[CharacterSheet]:
    """
    List all available pre-generated characters.

    Returns:
        List of character sheets for selection

    Raises:
        HTTPException: If characters data cannot be loaded
    """
    character_service = container.character_service
    try:
        characters = character_service.get_all_characters()
        return characters
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load characters: {e!s}") from e
