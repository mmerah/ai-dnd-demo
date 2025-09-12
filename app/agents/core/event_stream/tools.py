"""Handlers for tool-related events from PydanticAI (logging/capture only)."""

import json
import logging
from typing import Any, cast

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartStartEvent,
    ToolCallPart,
    ToolReturnPart,
)

from app.agents.core.event_stream.base import EventContext, EventHandler
from app.common.types import JSONSerializable
from app.interfaces.services.ai import IEventLoggerService

logger = logging.getLogger(__name__)


class ToolCallHandler(EventHandler):
    """Handles tool call events from the stream (capture + log only)."""

    def __init__(self, event_logger: IEventLoggerService):
        self.event_logger = event_logger

    async def can_handle(self, event: object) -> bool:
        if isinstance(event, PartStartEvent):
            return isinstance(event.part, ToolCallPart)
        return isinstance(event, FunctionToolCallEvent)

    async def handle(self, event: object, context: EventContext) -> None:
        if not isinstance(event, PartStartEvent | FunctionToolCallEvent):
            return
        tool_name, tool_call_id, args = self._extract_tool_info(event)
        if not tool_name:
            return

        if tool_call_id and tool_call_id in context.processed_tool_calls:
            logger.debug(f"Skipping duplicate tool call {tool_call_id} for {tool_name}")
            return

        processed_args = self._process_arguments(args)
        if processed_args is None:
            logger.debug(f"Skipping empty tool call for {tool_name}")
            return

        if tool_call_id:
            context.processed_tool_calls.add(tool_call_id)
            context.tool_calls_by_id[tool_call_id] = tool_name

        # Track if combat was started
        if tool_name in ["start_combat", "start_encounter_combat"]:
            context.combat_started = True
            logger.info(f"Combat started via {tool_name} - narrative agent should stop")

        self.event_logger.log_tool_call(tool_name, processed_args)
        logger.debug(f"Tool call captured (log only): {tool_name} with args: {processed_args}")

    def _extract_tool_info(self, event: object) -> tuple[str | None, str | None, Any]:
        """Extract tool info from supported event types with proper type narrowing."""
        if isinstance(event, PartStartEvent):
            part = event.part
            if isinstance(part, ToolCallPart):
                return (
                    part.tool_name,
                    part.tool_call_id,
                    part.args if part.args is not None else {},
                )
            # Not a tool call part
        if isinstance(event, FunctionToolCallEvent):
            part = event.part
            if isinstance(part, ToolCallPart):
                return (
                    part.tool_name,
                    part.tool_call_id,
                    part.args if part.args is not None else {},
                )
            # Not a tool call part
        return None, None, None

    def _process_arguments(self, args: Any) -> dict[str, JSONSerializable] | None:
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
        return {"raw_args": str(args)}


class ToolResultHandler(EventHandler):
    """Handles tool result events from the stream (capture + log only)."""

    def __init__(self, event_logger: IEventLoggerService):
        self.event_logger = event_logger

    async def can_handle(self, event: object) -> bool:
        return isinstance(event, FunctionToolResultEvent)

    async def handle(self, event: object, context: EventContext) -> None:
        if not isinstance(event, FunctionToolResultEvent):
            return
        result = event.result
        if not isinstance(result, ToolReturnPart):
            logger.debug("Tool result is not ToolReturnPart, skipping")
            return
        if result.tool_call_id not in context.tool_calls_by_id:
            logger.error(f"Tool result event has unmapped tool_call_id: {result.tool_call_id}")
            return

        tool_name = context.tool_calls_by_id[result.tool_call_id]
        result_str = self._get_result_string(result)
        self.event_logger.log_tool_result(tool_name, result_str)
        logger.debug(f"Tool result processed: {tool_name} -> {result_str[:100]}")

    def _get_result_string(self, result: Any) -> str:
        if isinstance(result, ToolReturnPart):
            return str(result.content)
        return str(result)


class ToolEventHandler:
    """Composite for tool call and result handlers (capture + log only)."""

    def __init__(self, event_logger: IEventLoggerService):
        self.tool_call_handler = ToolCallHandler(event_logger)
        self.tool_result_handler = ToolResultHandler(event_logger)

    def get_handlers(self) -> list[EventHandler]:
        return [self.tool_call_handler, self.tool_result_handler]
