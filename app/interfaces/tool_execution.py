"""Interfaces for tool execution tracking and validation."""

from abc import ABC, abstractmethod

from app.models.tool_results import ToolErrorResult


class IToolExecutionContext(ABC):
    """Interface for tool execution context that tracks call counts."""

    @abstractmethod
    def get_call_count(self, tool_name: str) -> int:
        """Get current call count for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Number of times the tool has been called in this execution
        """
        ...

    @abstractmethod
    def increment_call_count(self, tool_name: str) -> int:
        """Increment call count for a tool and return new count.

        Args:
            tool_name: Name of the tool

        Returns:
            New call count after increment
        """
        ...


class IToolExecutionGuard(ABC):
    """Interface for service that validates tool execution rules."""

    @abstractmethod
    def validate_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> ToolErrorResult | None:
        """Validate if a tool call should be allowed.

        Args:
            tool_name: Name of the tool being called
            context: Execution context tracking call counts

        Returns:
            ToolErrorResult if validation fails, None if allowed
        """
        ...

    @abstractmethod
    def record_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> None:
        """Record that a tool was called (increment counter).

        Call this AFTER validation passes and BEFORE executing the tool.

        Args:
            tool_name: Name of the tool
            context: Execution context to update
        """
        ...
