"""Centralized message display service following SOLID principles."""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.game_state import JSONSerializable
from app.services.broadcast_service import broadcast_service

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages that can be displayed."""

    NARRATIVE = "narrative"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DICE_ROLL = "dice_roll"
    CHARACTER_UPDATE = "character_update"
    COMBAT_UPDATE = "combat_update"
    SYSTEM = "system"
    ERROR = "error"
    GAME_UPDATE = "game_update"
    INITIAL_NARRATIVE = "initial_narrative"


class MessageService:
    """Service for managing and broadcasting all game messages."""

    async def send_narrative(
        self, game_id: str, content: str, is_chunk: bool = False, is_complete: bool = False
    ) -> None:
        """
        Send narrative content to the chat.

        Args:
            game_id: Game identifier
            content: Narrative text or chunk
            is_chunk: Whether this is a streaming chunk
            is_complete: Whether the narrative is complete
        """
        # Any is needed here because SSE event data varies by event type:
        # - "word": str for streaming chunks
        # - "complete": bool to signal completion
        # - "start": bool to signal start
        # - "content": str for initial content
        data: dict[str, Any] = {}
        if is_chunk:
            data["word"] = content
        elif is_complete:
            data["complete"] = True
        else:
            data["start"] = True
            if content:
                data["content"] = content

        await broadcast_service.publish(game_id, MessageType.NARRATIVE.value, data)

    async def send_initial_narrative(self, game_id: str, scenario_title: str, narrative: str) -> None:
        """
        Send the initial narrative when a game starts.

        Args:
            game_id: Game identifier
            scenario_title: Title of the scenario
            narrative: Initial narrative text
        """
        await broadcast_service.publish(
            game_id,
            MessageType.INITIAL_NARRATIVE.value,
            {"scenario_title": scenario_title, "narrative": narrative, "timestamp": datetime.utcnow().isoformat()},
        )

    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, Any]) -> None:
        """
        Send tool call information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool being called
            parameters: Tool parameters
        """
        await broadcast_service.publish(
            game_id,
            MessageType.TOOL_CALL.value,
            {"tool_name": tool_name, "parameters": parameters, "timestamp": datetime.utcnow().isoformat()},
        )

    async def send_tool_result(self, game_id: str, tool_name: str, result: JSONSerializable) -> None:
        """
        Send tool result information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool that was called
            result: Result from the tool
        """
        await broadcast_service.publish(
            game_id,
            MessageType.TOOL_RESULT.value,
            {"tool_name": tool_name, "result": result, "timestamp": datetime.utcnow().isoformat()},
        )

    async def send_dice_roll(
        self, game_id: str, roll_type: str, dice: str, modifier: int, result: int, details: dict[str, Any] | None = None
    ) -> None:
        """
        Send dice roll result to the chat.

        Args:
            game_id: Game identifier
            roll_type: Type of roll (attack, damage, save, etc.)
            dice: Dice notation (e.g., "1d20")
            modifier: Modifier applied to the roll
            result: Final result
            details: Additional details about the roll
        """
        await broadcast_service.publish(
            game_id,
            MessageType.DICE_ROLL.value,
            {
                "roll_type": roll_type,
                "dice": dice,
                "modifier": modifier,
                "result": result,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def send_character_update(self, game_id: str, character_data: dict[str, Any]) -> None:
        """
        Send character sheet update.

        Args:
            game_id: Game identifier
            character_data: Updated character data
        """
        await broadcast_service.publish(game_id, MessageType.CHARACTER_UPDATE.value, {"character": character_data})

    async def send_combat_update(self, game_id: str, combat_data: dict[str, Any]) -> None:
        """
        Send combat state update.

        Args:
            game_id: Game identifier
            combat_data: Combat state data
        """
        await broadcast_service.publish(game_id, MessageType.COMBAT_UPDATE.value, combat_data)

    async def send_system_message(self, game_id: str, message: str, level: str = "info") -> None:
        """
        Send system message to the chat.

        Args:
            game_id: Game identifier
            message: System message text
            level: Message level (info, warning, error)
        """
        await broadcast_service.publish(
            game_id,
            MessageType.SYSTEM.value,
            {"message": message, "level": level, "timestamp": datetime.utcnow().isoformat()},
        )

    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        """
        Send error message to the chat.

        Args:
            game_id: Game identifier
            error: Error message
            error_type: Type of error if available
        """
        await broadcast_service.publish(
            game_id,
            MessageType.ERROR.value,
            {"error": error, "type": error_type, "timestamp": datetime.utcnow().isoformat()},
        )

    async def send_game_update(self, game_id: str, game_state_data: dict[str, Any]) -> None:
        """
        Send complete game state update.

        Args:
            game_id: Game identifier
            game_state_data: Complete game state data
        """
        await broadcast_service.publish(game_id, MessageType.GAME_UPDATE.value, game_state_data)

    async def send_scenario_info(
        self, game_id: str, scenario_title: str, scenario_id: str, available_scenarios: list[dict[str, str]]
    ) -> None:
        """
        Send scenario information to the frontend.

        Args:
            game_id: Game identifier
            scenario_title: Title of current scenario
            scenario_id: ID of current scenario
            available_scenarios: List of available scenarios
        """
        from app.models.game_state import JSONSerializable

        scenarios_data: JSONSerializable = available_scenarios  # type: ignore[assignment]
        await broadcast_service.publish(
            game_id,
            "scenario_info",
            {
                "current_scenario": {"id": scenario_id, "title": scenario_title},
                "available_scenarios": scenarios_data,
            },
        )


# Create singleton instance
message_service = MessageService()
