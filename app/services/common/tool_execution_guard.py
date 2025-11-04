"""Service for validating tool execution rules."""

import logging

from app.interfaces.tool_execution import IToolExecutionContext, IToolExecutionGuard
from app.models.tool_results import ToolErrorResult

logger = logging.getLogger(__name__)


class ToolExecutionGuard(IToolExecutionGuard):
    """Service for validating tool execution rules.

    Encapsulates business rules about tool usage:
    - How many times a tool can be called per execution
    - Which tools are mutually exclusive
    - Tool call ordering constraints
    """

    # Tools that can only be called once per agent execution
    SINGLE_USE_TOOLS = frozenset(["next_turn", "end_combat"])

    def __init__(self) -> None:
        """Initialize the guard."""
        pass

    def validate_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> ToolErrorResult | None:
        # Check single-use tools
        if tool_name in self.SINGLE_USE_TOOLS:
            current_count = context.get_call_count(tool_name)

            if current_count > 0:
                error_msg = (
                    f"BLOCKED: {tool_name} has already been called {current_count} time(s) "
                    f"in this agent response. You can only call {tool_name} ONCE per turn."
                )

                suggestion = self._get_suggestion_for_tool(tool_name)

                logger.error(f"[TOOL_GUARD] {error_msg}")

                return ToolErrorResult(
                    error=error_msg,
                    tool_name=tool_name,
                    suggestion=suggestion,
                )

        # All validations passed
        return None

    def _get_suggestion_for_tool(self, tool_name: str) -> str:
        """Get helpful suggestion for blocked tool."""
        suggestions = {
            "next_turn": (
                "Remove duplicate next_turn calls. Only call next_turn once after completing the turn. "
                "Multiple next_turn calls skip turns and break combat order."
            ),
            "end_combat": (
                "Remove duplicate end_combat calls. Only call end_combat once when all enemies are defeated."
            ),
        }
        return suggestions.get(
            tool_name,
            f"Remove duplicate {tool_name} calls. This tool can only be called once per turn.",
        )

    def record_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> None:
        new_count = context.increment_call_count(tool_name)
        logger.debug(f"[TOOL_GUARD] {tool_name} call #{new_count} recorded in execution context")
