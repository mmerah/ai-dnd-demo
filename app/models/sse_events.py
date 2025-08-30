"""SSE event models for type-safe event broadcasting."""

from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.game_state import JSONSerializable


class SSEEventType(str, Enum):
    """All possible SSE event types."""

    CONNECTED = "connected"
    HEARTBEAT = "heartbeat"
    NARRATIVE = "narrative"
    INITIAL_NARRATIVE = "initial_narrative"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DICE_ROLL = "dice_roll"
    CHARACTER_UPDATE = "character_update"
    COMBAT_UPDATE = "combat_update"
    SYSTEM = "system"
    ERROR = "error"
    GAME_UPDATE = "game_update"
    LOCATION_UPDATE = "location_update"
    QUEST_UPDATE = "quest_update"
    ACT_UPDATE = "act_update"
    SCENARIO_INFO = "scenario_info"
    COMPLETE = "complete"


class BaseSSEData(BaseModel):
    """Base class for SSE event data."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConnectedData(BaseSSEData):
    """Data for connected event."""

    game_id: str
    status: Literal["connected"]


class HeartbeatData(BaseSSEData):
    """Data for heartbeat event."""

    pass  # Empty data for heartbeat


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


class ToolCallData(BaseSSEData):
    """Data for tool call events."""

    tool_name: str
    parameters: dict[str, JSONSerializable]


class ToolResultData(BaseSSEData):
    """Data for tool result events."""

    tool_name: str
    result: JSONSerializable


class DiceRollData(BaseSSEData):
    """Data for dice roll events."""

    roll_type: str
    dice: str
    modifier: int
    result: int
    details: dict[str, JSONSerializable] = Field(default_factory=dict)


class CharacterUpdateData(BaseSSEData):
    """Data for character update events - wraps CharacterSheet.model_dump()."""

    character: dict[str, JSONSerializable]


class CombatUpdateData(BaseSSEData):
    """Data for combat update events - wraps CombatState.model_dump()."""

    combat: dict[str, JSONSerializable]


class SystemMessageData(BaseSSEData):
    """Data for system message events."""

    message: str
    level: Literal["info", "warning", "error"] = "info"


class ErrorData(BaseSSEData):
    """Data for error events."""

    error: str
    type: str | None = None


class GameUpdateData(BaseSSEData):
    """Data for complete game state update events - wraps GameState.model_dump().

    This wraps the entire GameState as a dictionary to avoid duplicating
    the GameState model structure and maintain DRY principles.
    """

    # The entire GameState.model_dump() result
    game_state: dict[str, JSONSerializable]


class ConnectionInfo(BaseModel):
    """Information about a location connection."""

    to_location_id: str
    description: str
    direction: str | None = None
    is_accessible: bool = True
    is_visible: bool = True


class LocationUpdateData(BaseSSEData):
    """Data for location update events."""

    location_id: str
    location_name: str
    description: str
    connections: list[ConnectionInfo]
    danger_level: str
    npcs_present: list[str]


class QuestUpdateData(BaseSSEData):
    """Data for quest update events - wraps quest data."""

    active_quests: list[dict[str, JSONSerializable]]  # List of Quest.model_dump() results
    completed_quest_ids: list[str]


class ActUpdateData(BaseSSEData):
    """Data for act update events."""

    act_id: str
    act_name: str
    act_index: int


class ScenarioSummary(BaseModel):
    """Summary information for a scenario."""

    id: str
    title: str
    description: str | None = None


class ScenarioInfoData(BaseSSEData):
    """Data for scenario info events."""

    current_scenario: ScenarioSummary
    available_scenarios: list[ScenarioSummary]


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
    | DiceRollData
    | CharacterUpdateData
    | CombatUpdateData
    | SystemMessageData
    | ErrorData
    | GameUpdateData
    | LocationUpdateData
    | QuestUpdateData
    | ActUpdateData
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
