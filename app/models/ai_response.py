"""AI Response models for streaming and display."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.common.types import JSONSerializable


class NarrativeChunkResponse(BaseModel):
    """Response for narrative chunks."""

    type: Literal["narrative_chunk"] = "narrative_chunk"
    content: str


class CompleteResponse(BaseModel):
    """Response for complete narrative."""

    type: Literal["complete"] = "complete"
    narrative: str


class ErrorResponse(BaseModel):
    """Response for errors."""

    type: Literal["error"] = "error"
    message: str


AIResponse = NarrativeChunkResponse | CompleteResponse | ErrorResponse


class StreamEventType(Enum):
    """Types of events that can be streamed."""

    NARRATIVE_CHUNK = "narrative_chunk"
    THINKING = "thinking"
    COMPLETE = "complete"
    ERROR = "error"


class NarrativeResponse(BaseModel):
    """Complete narrative response from the AI."""

    narrative: str
    thinking: str | None = None
    usage: dict[str, JSONSerializable] | None = None


StreamEventContent = (
    str  # For narrative chunks and error messages
    | NarrativeResponse  # For the complete response
)


class StreamEvent(BaseModel):
    """Base event for streaming responses."""

    type: StreamEventType
    content: StreamEventContent
    metadata: dict[str, JSONSerializable] = Field(default_factory=dict)
