from typing import Optional
from pydantic import BaseModel, Field


class NewGameRequest(BaseModel):
    """Request model for creating a new game."""
    character_id: str = Field(..., description="ID of the character to play")
    premise: Optional[str] = Field(
        None, 
        description="Optional custom premise for the adventure"
    )
    scenario_id: Optional[str] = Field(
        None,
        description="ID of the scenario to play"
    )


class NewGameResponse(BaseModel):
    """Response model for new game creation."""
    game_id: str = Field(..., description="Unique identifier for the game")


class PlayerActionRequest(BaseModel):
    """Request model for player actions."""
    message: str = Field(..., description="Player's message/action")