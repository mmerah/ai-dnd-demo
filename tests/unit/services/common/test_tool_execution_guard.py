"""Unit tests for ToolExecutionGuard service."""

from app.services.common.tool_execution_context import ToolExecutionContext
from app.services.common.tool_execution_guard import ToolExecutionGuard


class TestToolExecutionGuard:
    """Test suite for ToolExecutionGuard validation logic."""

    def setup_method(self) -> None:
        """Set up fresh instances for each test."""
        self.guard = ToolExecutionGuard()
        self.context = ToolExecutionContext()

    def test_first_call_allowed(self) -> None:
        """First call to a single-use tool should be allowed."""
        result = self.guard.validate_tool_call("next_turn", self.context)
        assert result is None

    def test_second_call_blocked(self) -> None:
        """Second call to a single-use tool should be blocked."""
        self.guard.record_tool_call("next_turn", self.context)
        result = self.guard.validate_tool_call("next_turn", self.context)

        assert result is not None
        assert result.tool_name == "next_turn"
        assert "BLOCKED" in result.error
        assert result.suggestion is not None

    def test_normal_tool_unlimited_calls(self) -> None:
        """Non-single-use tools should allow unlimited calls."""
        for _ in range(5):
            assert self.guard.validate_tool_call("attack", self.context) is None
            self.guard.record_tool_call("attack", self.context)

    def test_record_increments_count(self) -> None:
        """record_tool_call should increment the counter."""
        assert self.context.get_call_count("test_tool") == 0
        self.guard.record_tool_call("test_tool", self.context)
        assert self.context.get_call_count("test_tool") == 1

    def test_fresh_context_resets_validation(self) -> None:
        """Fresh context should allow tool that was blocked in previous execution."""
        self.guard.record_tool_call("next_turn", self.context)
        assert self.guard.validate_tool_call("next_turn", self.context) is not None

        new_context = ToolExecutionContext()
        assert self.guard.validate_tool_call("next_turn", new_context) is None
