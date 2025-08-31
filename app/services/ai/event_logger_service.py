"""Service for logging agent events following Single Responsibility."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EventLoggerService:
    """Service for logging agent events following Single Responsibility."""

    def __init__(self, game_id: str = "", debug: bool = False):
        self.game_id = game_id
        self.debug = debug

    def log_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        logger.info(f"[TOOL_CALL] {tool_name}: {args}")

    def log_tool_result(self, tool_name: str, result: str) -> None:
        logger.info(f"[TOOL_RESULT] {tool_name}: {result}")

    def log_thinking(self, content: str) -> None:
        if self.debug:
            logger.debug(f"[THINKING] {content}")

    def log_error(self, error: Exception) -> None:
        logger.error(f"[ERROR] {type(error).__name__}: {error!s}", exc_info=True)
