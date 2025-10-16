"""SSE event models for type-safe event broadcasting."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.common.types import JSONSerializable
from app.models.combat import CombatState, CombatSuggestion
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
    COMBAT_SUGGESTION = "combat_suggestion"
    SYSTEM = "system"
    NPC_DIALOGUE = "npc_dialogue"
    POLICY_WARNING = "policy_warning"
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


class ToolCallData(BaseSSEData):
    """Data for tool call events."""

    tool_name: str
    parameters: dict[str, JSONSerializable]


class ToolResultData(BaseSSEData):
    """Data for tool result events."""

    tool_name: str
    result: ToolResult


class NPCDialogueData(BaseSSEData):
    """Data for NPC dialogue events."""

    npc_id: str
    npc_name: str
    content: str
    complete: bool = True


class CombatUpdateData(BaseSSEData):
    """Data for combat update events."""

    combat: CombatState


class CombatSuggestionData(BaseSSEData):
    """Data for combat suggestion events from allied NPCs."""

    suggestion: CombatSuggestion


class SystemMessageData(BaseSSEData):
    """Data for system message events."""

    message: str
    level: Literal["info", "warning", "error"] = "info"


class PolicyWarningData(BaseSSEData):
    """Data for explicit policy warning events (tool gating, etc.)."""

    message: str
    tool_name: str | None = None
    agent_type: str | None = None


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
    | NPCDialogueData
    | CombatUpdateData
    | CombatSuggestionData
    | SystemMessageData
    | PolicyWarningData
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
