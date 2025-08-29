from pydantic import BaseModel, Field


class NewGameRequest(BaseModel):
    """Request model for creating a new game."""

    character_id: str = Field(..., description="ID of the character to play")
    premise: str | None = Field(None, description="Optional custom premise for the adventure")
    scenario_id: str | None = Field(None, description="ID of the scenario to play")


class NewGameResponse(BaseModel):
    """Response model for new game creation."""

    game_id: str = Field(..., description="Unique identifier for the game")


class PlayerActionRequest(BaseModel):
    """Request model for player actions."""

    message: str = Field(..., description="Player's message/action")
