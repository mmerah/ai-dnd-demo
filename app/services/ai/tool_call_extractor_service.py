"""Service for extracting and executing tool calls from narrative text."""

import logging
import re
from typing import Any

from app.agents.core.types import AgentType
from app.events.base import BaseCommand
from app.events.commands.combat_commands import (
    EndCombatCommand,
    NextTurnCommand,
)
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IToolCallExtractorService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class ToolCallExtractorService(IToolCallExtractorService):
    """Service for extracting and executing tool calls from narrative text."""

    def __init__(self, event_bus: IEventBus):
        """Initialize the service.

        Args:
            event_bus: Event bus for executing commands
        """
        self.event_bus = event_bus
        # Only look for JSON code blocks and match allowlisted tool names inside
        self.codeblock_pattern = re.compile(r"```json\s*\n(.*?)\n\s*```", re.MULTILINE | re.DOTALL)
        self.allowlist = {"next_turn", "end_combat"}

    def extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        tool_calls: list[dict[str, Any]] = []
        # Find all JSON code blocks and look for allowlisted function names in the raw content
        for match in self.codeblock_pattern.finditer(text):
            content = match.group(1)
            for fn in self.allowlist:
                if fn in content:
                    tool_calls.append({"function": fn, "arguments": {}})
                    logger.info(f"Matched allowlisted tool in JSON block: {fn}")
        return tool_calls

    async def execute_extracted_tool_call(
        self,
        tool_call: dict[str, Any],
        game_state: GameState,
        agent_type: AgentType,
    ) -> bool:
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})

        logger.info(f"Executing extracted tool call: {function_name} with args: {arguments}")

        try:
            command: BaseCommand | None = None

            # Only handle critical combat flow tools
            if function_name == "next_turn":
                command = NextTurnCommand(
                    game_id=game_state.game_id,
                    agent_type=agent_type,
                )
                logger.warning(f"AI output tool call as JSON instead of calling it properly: {function_name}")
            elif function_name == "end_combat":
                command = EndCombatCommand(
                    game_id=game_state.game_id,
                    agent_type=agent_type,
                )
                logger.warning(f"AI output tool call as JSON instead of calling it properly: {function_name}")
            else:
                # Warn about other tool calls but don't execute them
                logger.warning(
                    f"Found tool call '{function_name}' in narrative output but not executing it. "
                    f"The AI should call tools properly, not output them as JSON."
                )
                return False

            # Execute the command
            await self.event_bus.submit_and_wait([command])
            logger.info(f"Successfully executed extracted tool call: {function_name}")
            return True

        except Exception as e:
            logger.error(f"Error executing extracted tool call {function_name}: {e}")
            return False
