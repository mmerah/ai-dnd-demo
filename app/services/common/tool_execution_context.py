"""Execution context for tracking tool calls within an agent execution."""

from dataclasses import dataclass, field

from app.interfaces.tool_execution import IToolExecutionContext


@dataclass
class ToolExecutionContext(IToolExecutionContext):
    """Tracks tool execution state for a single agent execution.

    Lifetime: One agent execution (created fresh for each agent.process() call).
    Business logic lives in ToolExecutionGuard.
    """

    # Track how many times each tool has been called in this execution
    tool_call_counts: dict[str, int] = field(default_factory=dict)

    def increment_call_count(self, tool_name: str) -> int:
        """Increment call count for a tool and return new count."""
        current_count = self.tool_call_counts.get(tool_name, 0)
        new_count = current_count + 1
        self.tool_call_counts[tool_name] = new_count
        return new_count

    def get_call_count(self, tool_name: str) -> int:
        """Get current call count for a tool."""
        return self.tool_call_counts.get(tool_name, 0)

    def reset(self) -> None:
        """Reset all counters (typically not needed - create new instance instead)."""
        self.tool_call_counts.clear()
