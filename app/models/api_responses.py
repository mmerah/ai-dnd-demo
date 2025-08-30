"""API response models for type-safe REST endpoint responses."""

from typing import Literal

from pydantic import BaseModel, Field


class GameStatusResponse(BaseModel):
    """Response for game status operations."""

    game_id: str
    status: Literal["resumed", "created", "loaded"]


class ActionAcknowledgement(BaseModel):
    """Response acknowledging a player action."""

    status: Literal["action received", "processing"]


class SavedGameSummary(BaseModel):
    """Summary of a saved game for listing."""

    game_id: str
    character_name: str
    location: str
    last_played: str
    scenario_title: str | None = None


class ScenarioDetailResponse(BaseModel):
    """Detailed scenario information."""

    id: str
    title: str
    description: str
    starting_location: str


class ScenarioSummaryResponse(BaseModel):
    """Summary of a scenario for listing."""

    id: str
    title: str
    description: str | None = None


class ItemDetailResponse(BaseModel):
    """Detailed item information."""

    name: str
    type: str
    rarity: str
    weight: float
    value: float  # Value in gold pieces (can be fractional)
    description: str
    damage: str | None = None
    damage_type: str | None = None
    properties: list[str] = Field(default_factory=list)
    armor_class: int | None = None


class SpellDetailResponse(BaseModel):
    """Detailed spell information."""

    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    higher_levels: str | None = None
    classes: list[str]
    ritual: bool = False
    concentration: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    type: str | None = None
    detail: str | None = None
