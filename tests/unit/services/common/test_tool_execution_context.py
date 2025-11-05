"""Unit tests for ToolExecutionContext."""

from app.services.common.tool_execution_context import ToolExecutionContext


class TestToolExecutionContext:
    """Test suite for ToolExecutionContext state tracking."""

    def setup_method(self) -> None:
        """Set up fresh context for each test."""
        self.context = ToolExecutionContext()

    def test_initial_state_empty(self) -> None:
        """New context should start with no recorded calls."""
        assert self.context.get_call_count("any_tool") == 0

    def test_increment_returns_new_count(self) -> None:
        """increment_call_count should return the new count."""
        assert self.context.increment_call_count("tool") == 1
        assert self.context.increment_call_count("tool") == 2
        assert self.context.increment_call_count("tool") == 3

    def test_get_call_count_accuracy(self) -> None:
        """get_call_count should return accurate count."""
        self.context.increment_call_count("tool")
        self.context.increment_call_count("tool")
        assert self.context.get_call_count("tool") == 2

    def test_multiple_tools_independent(self) -> None:
        """Each tool should have its own independent counter."""
        self.context.increment_call_count("tool_a")
        self.context.increment_call_count("tool_a")
        self.context.increment_call_count("tool_b")

        assert self.context.get_call_count("tool_a") == 2
        assert self.context.get_call_count("tool_b") == 1

    def test_reset_clears_all(self) -> None:
        """reset() should clear all recorded calls."""
        self.context.increment_call_count("tool_a")
        self.context.increment_call_count("tool_b")

        self.context.reset()

        assert self.context.get_call_count("tool_a") == 0
        assert self.context.get_call_count("tool_b") == 0
