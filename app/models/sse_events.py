"""SSE event models for type-safe event broadcasting."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.common.types import JSONSerializable
from app.models.combat import CombatState
from app.models.game_state import GameState
from app.models.scenario import ScenarioSheet
from app.models.tool_results import ToolResult


class SSEEventType(str, Enum):
    """All possible SSE event types."""

    CONNECTED = "connected"
    HEARTBEAT = "heartbeat"
    NARRATIVE = "narrative"
    INITIAL_NARRATIVE = "initial_narrative"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DICE_ROLL = "dice_roll"
    COMBAT_UPDATE = "combat_update"
    SYSTEM = "system"
    ERROR = "error"
    GAME_UPDATE = "game_update"
    SCENARIO_INFO = "scenario_info"
    COMPLETE = "complete"


class BaseSSEData(BaseModel):
    """Base class for SSE event data."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectedData(BaseSSEData):
    """Data for connected event."""

    game_id: str
    status: Literal["connected"]


class HeartbeatData(BaseSSEData):
    """Data for heartbeat event."""

    # Empty data for heartbeat


class NarrativeData(BaseSSEData):
    """Data for narrative streaming events."""

    word: str | None = None
    complete: bool | None = None
    start: bool | None = None
    content: str | None = None


class InitialNarrativeData(BaseSSEData):
    """Data for initial narrative event."""

    scenario_title: str
    narrative: str


# TODO: Verify ToolCallData vs ToolResultData vs ToolResult
# TODO: Generally, those SSE events, are they useful ?
class ToolCallData(BaseSSEData):
    """Data for tool call events."""

    tool_name: str
    parameters: dict[str, JSONSerializable]


class ToolResultData(BaseSSEData):
    """Data for tool result events."""

    tool_name: str
    result: ToolResult


class CombatUpdateData(BaseSSEData):
    """Data for combat update events."""

    combat: CombatState


class SystemMessageData(BaseSSEData):
    """Data for system message events."""

    message: str
    level: Literal["info", "warning", "error"] = "info"


class ErrorData(BaseSSEData):
    """Data for error events."""

    error: str
    type: str | None = None


class GameUpdateData(BaseSSEData):
    """Data for complete game state update events."""

    game_state: GameState


class ScenarioInfoData(BaseSSEData):
    """Data for scenario info events."""

    current_scenario: ScenarioSheet
    available_scenarios: list[ScenarioSheet]


class CompleteData(BaseSSEData):
    """Data for completion events."""

    status: Literal["success", "error"]


# Union type for all possible SSE data types
SSEData = (
    ConnectedData
    | HeartbeatData
    | NarrativeData
    | InitialNarrativeData
    | ToolCallData
    | ToolResultData
    | CombatUpdateData
    | SystemMessageData
    | ErrorData
    | GameUpdateData
    | ScenarioInfoData
    | CompleteData
)


class SSEEvent(BaseModel):
    """Fully typed SSE event."""

    event: SSEEventType
    data: SSEData

    def to_sse_format(self) -> dict[str, str]:
        """
        Convert to SSE wire format for transmission.

        Returns:
            Dictionary with event and data fields for SSE
        """
        return {"event": self.event.value, "data": self.data.model_dump_json()}

    @classmethod
    def create_connected(cls, game_id: str) -> "SSEEvent":
        """Create a connected event."""
        return cls(event=SSEEventType.CONNECTED, data=ConnectedData(game_id=game_id, status="connected"))

    @classmethod
    def create_heartbeat(cls) -> "SSEEvent":
        """Create a heartbeat event."""
        return cls(event=SSEEventType.HEARTBEAT, data=HeartbeatData())

    @classmethod
    def create_error(cls, error: str, error_type: str | None = None) -> "SSEEvent":
        """Create an error event."""
        return cls(event=SSEEventType.ERROR, data=ErrorData(error=error, type=error_type))

    @classmethod
    def create_complete(cls, status: Literal["success", "error"] = "success") -> "SSEEvent":
        """Create a completion event."""
        return cls(event=SSEEventType.COMPLETE, data=CompleteData(status=status))
