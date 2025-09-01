"""Handler for tool-related events from PydanticAI."""

import json
import logging
from typing import Any, cast

from pydantic import BaseModel
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartStartEvent,
    ToolCallPart,
)

from app.agents.event_handlers.base import EventContext, EventHandler
from app.common.types import JSONSerializable
from app.models.ai_response import CapturedToolEvent
from app.services.ai.event_logger_service import EventLoggerService

logger = logging.getLogger(__name__)


class ToolCallHandler(EventHandler):
    """Handles tool call events from the stream."""

    def __init__(self, event_logger: EventLoggerService | None = None):
        self.event_logger = event_logger

    async def can_handle(self, event: object) -> bool:
        """Check if this is a tool call event."""
        if isinstance(event, PartStartEvent):
            return isinstance(event.part, ToolCallPart)
        if isinstance(event, FunctionToolCallEvent):
            return hasattr(event, "part") and hasattr(event.part, "tool_name")
        return False

    async def handle(self, event: object, context: EventContext) -> None:
        """Process tool call event."""
        # Type narrowing happens in can_handle, but we check again for safety
        if not isinstance(event, PartStartEvent | FunctionToolCallEvent):
            return
        tool_name, tool_call_id, args = self._extract_tool_info(event)

        if not tool_name:
            return

        # Check for duplicate processing
        if tool_call_id and tool_call_id in context.processed_tool_calls:
            logger.debug(f"Skipping duplicate tool call {tool_call_id} for {tool_name}")
            return

        # Process arguments first to check if they're empty
        processed_args = self._process_arguments(args)
        if processed_args is None:
            logger.debug(f"Skipping empty tool call for {tool_name}")
            # Don't mark as processed if arguments are empty
            return

        # Track the tool call only after confirming it has valid arguments
        if tool_call_id:
            context.processed_tool_calls.add(tool_call_id)
            context.tool_calls_by_id[tool_call_id] = tool_name

        # Log and capture the event
        if self.event_logger:
            self.event_logger.log_tool_call(tool_name, processed_args)

        context.captured_tool_events.append(CapturedToolEvent(tool_name=tool_name, parameters=processed_args))
        logger.debug(f"Tool call captured: {tool_name} with args: {processed_args}")

    def _extract_tool_info(self, event: object) -> tuple[str | None, str | None, Any]:
        """Extract tool information from various event types."""
        if (
            isinstance(event, PartStartEvent)
            and isinstance(event.part, ToolCallPart)
            or isinstance(event, FunctionToolCallEvent)
            and hasattr(event, "part")
            and hasattr(event.part, "tool_name")
        ):
            return (
                event.part.tool_name,
                getattr(event.part, "tool_call_id", None),
                getattr(event.part, "args", {}),
            )
        return None, None, None

    def _process_arguments(self, args: Any) -> dict[str, JSONSerializable] | None:
        """Process and validate tool arguments."""
        if not args or args == "" or args == {}:
            return None

        if isinstance(args, dict):
            return cast(dict[str, JSONSerializable], args)

        if isinstance(args, str):
            args_str = args.strip()
            if not args_str:
                return None
            try:
                parsed = json.loads(args_str)
                if isinstance(parsed, dict):
                    return cast(dict[str, JSONSerializable], parsed)
            except (json.JSONDecodeError, ValueError):
                pass
            return {"raw_args": args_str}

        # Fallback for other types
        return {"raw_args": str(args)}


class ToolResultHandler(EventHandler):
    """Handles tool result events from the stream."""

    def __init__(self, event_logger: EventLoggerService | None = None):
        self.event_logger = event_logger

    async def can_handle(self, event: object) -> bool:
        """Check if this is a tool result event."""
        return isinstance(event, FunctionToolResultEvent)

    async def handle(self, event: object, context: EventContext) -> None:
        """Process tool result event."""
        if not isinstance(event, FunctionToolResultEvent):
            return
        # Get tool name from tracking
        tool_name = "unknown"
        if hasattr(event, "tool_call_id") and event.tool_call_id in context.tool_calls_by_id:
            tool_name = context.tool_calls_by_id[event.tool_call_id]

        if not hasattr(event, "result"):
            return

        result = event.result

        # Log the result
        result_str = self._get_result_string(result)
        if self.event_logger:
            self.event_logger.log_tool_result(tool_name, result_str)

        # Update the corresponding tool call event
        self._update_tool_event_with_result(tool_name, result, context)

        logger.debug(f"Tool result processed: {tool_name} -> {result_str[:100]}")

    def _get_result_string(self, result: Any) -> str:
        """Get string representation of result."""
        if hasattr(result, "content"):
            return str(result.content)
        return str(result)

    def _update_tool_event_with_result(self, tool_name: str, result: Any, context: EventContext) -> None:
        """Update the captured tool event with its result."""
        for event in reversed(context.captured_tool_events):
            if event.tool_name == tool_name and event.result is None:
                # Try to extract the actual result model
                if hasattr(result, "content") and isinstance(result.content, BaseModel):
                    # This might be a ToolResult subtype
                    try:
                        event.result = result.content  # type: ignore[assignment]
                    except Exception:
                        logger.warning(f"Could not assign result for tool {tool_name}")
                else:
                    logger.debug(f"Result for {tool_name} is not a recognized type")
                break


class ToolEventHandler:
    """Composite handler for all tool-related events."""

    def __init__(self, event_logger: EventLoggerService | None = None):
        self.tool_call_handler = ToolCallHandler(event_logger)
        self.tool_result_handler = ToolResultHandler(event_logger)

    def get_handlers(self) -> list[EventHandler]:
        """Get all tool event handlers."""
        return [self.tool_call_handler, self.tool_result_handler]
