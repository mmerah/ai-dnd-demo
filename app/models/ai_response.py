"""AI Response models for streaming and display."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    COMPLETE = "complete"
    ERROR = "error"


class StreamEvent(BaseModel):
    """Base event for streaming responses."""

    type: StreamEventType
    content: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCallEvent(BaseModel):
    """Event for tool calls."""

    tool_name: str
    args: dict[str, Any]
    tool_call_id: str | None = None


class ToolResultEvent(BaseModel):
    """Event for tool results."""

    tool_name: str
    result: Any
    tool_call_id: str | None = None


class NarrativeResponse(BaseModel):
    """Complete narrative response from the AI."""

    narrative: str
    tool_calls: list[ToolCallEvent] = Field(default_factory=list)
    thinking: str | None = None
    usage: dict[str, int] | None = None
