"""Service for logging agent events."""

import logging
from typing import Any

from app.interfaces.services.ai import IEventLoggerService

logger = logging.getLogger(__name__)


class EventLoggerService(IEventLoggerService):
    """Service for logging agent events."""

    def __init__(self, game_id: str = "", debug: bool = False, agent_type: str = "unknown"):
        self.game_id = game_id
        self.debug = debug
        self.agent_type = agent_type

    def set_game_id(self, game_id: str) -> None:
        self.game_id = game_id

    def set_agent_type(self, agent_type: str) -> None:
        self.agent_type = agent_type

    def log_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        logger.info(f"[{self.agent_type.upper()}_TOOL_CALL] {tool_name}: {args}")

    def log_tool_result(self, tool_name: str, result: str) -> None:
        logger.info(f"[{self.agent_type.upper()}_TOOL_RESULT] {tool_name}: {result}")

    def log_thinking(self, content: str) -> None:
        if self.debug:
            logger.debug(f"[THINKING] {content}")

    def log_error(self, error: Exception) -> None:
        logger.error(f"[ERROR] {type(error).__name__}: {error!s}", exc_info=True)
