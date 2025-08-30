"""Common type definitions used across the application."""

from typing import Any

# Type alias for JSON-serializable data
# Used at boundaries where we need to serialize to JSON (SSE, file I/O, etc.)
JSONSerializable = str | int | float | bool | None | dict[str, Any] | list[Any]
