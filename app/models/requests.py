from pydantic import BaseModel, Field


class NewGameRequest(BaseModel):
    """Request model for creating a new game."""

    character_id: str = Field(..., description="ID of the character to play")
    premise: str | None = Field(None, description="Optional custom premise for the adventure")
    scenario_id: str | None = Field(None, description="ID of the scenario to play")


class NewGameResponse(BaseModel):
    """Response model for new game creation."""

    game_id: str = Field(..., description="Unique identifier for the game")


class ResumeGameResponse(BaseModel):
    """Response model for resuming a saved game."""

    game_id: str = Field(..., description="Unique identifier for the resumed game")
    status: str = Field(..., description="Resume status, typically 'resumed'")


class PlayerActionRequest(BaseModel):
    """Request model for player actions."""

    message: str = Field(..., description="Player's message/action")


class EquipItemRequest(BaseModel):
    """Request model to equip or unequip a specific inventory item for the player."""

    item_name: str = Field(..., description="Exact name of the item in inventory")
    equipped: bool = Field(..., description="True to equip one unit, False to unequip one unit")


class EquipItemResponse(BaseModel):
    """Response model for equip/unequip operations."""

    game_id: str
    item_name: str
    equipped_quantity: int
    new_armor_class: int
