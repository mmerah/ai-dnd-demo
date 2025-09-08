"""
Broadcast service for pub/sub SSE event streaming.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import cast

from pydantic import BaseModel

from app.interfaces.services.common import IBroadcastService
from app.models.sse_events import SSEData, SSEEvent, SSEEventType

logger = logging.getLogger(__name__)


class BroadcastService(IBroadcastService):
    """Service for broadcasting SSE events to connected clients."""

    def __init__(self) -> None:
        """Initialize the broadcast service with empty queues."""
        # Dictionary of game_id -> list of subscriber queues
        # Queues hold dict[str, str] because SSEEvent.to_sse_format() returns that
        self.subscribers: dict[str, list[asyncio.Queue[dict[str, str]]]] = defaultdict(list)

    async def publish(self, game_id: str, event: str, data: BaseModel) -> None:
        """
        Publish an event to all subscribers for a specific game.

        Args:
            game_id: The game identifier
            event: The event type (e.g., 'narrative', 'tool_result')
            data: The event data (Pydantic model)
        """
        # Get all subscriber queues for this game
        queues = self.subscribers.get(game_id, [])

        # Convert string event to SSEEventType
        event_type = SSEEventType(event)

        # Create the SSE event
        # Type narrowing: The interface uses BaseModel for genericity, but all callers
        # actually pass SSEData types (union of all SSE data models).
        # This is a deliberate design choice to keep the interface generic while the
        # implementation is specific. The cast is safe because we control all callers.
        sse_event = SSEEvent(event=event_type, data=cast(SSEData, data))
        sse_format = sse_event.to_sse_format()

        # Remove dead queues (full or closed)
        active_queues = []
        for queue in queues:
            try:
                # Try to put the event in the queue (non-blocking check first)
                queue.put_nowait(sse_format)
                active_queues.append(queue)
            except asyncio.QueueFull:
                # Queue is full, skip it (acceptable in pub/sub pattern)
                logger.warning(f"Dropping message for game {game_id} - queue full")
            except asyncio.InvalidStateError:
                # Queue is closed, expected behavior when client disconnects
                logger.warning(f"Dropping message for game {game_id} - client disconnected")
                pass

        # Update the subscriber list with only active queues
        if active_queues:
            self.subscribers[game_id] = active_queues
        else:
            # No active subscribers, remove the game entry
            self.subscribers.pop(game_id, None)

    async def subscribe(self, game_id: str) -> AsyncGenerator[dict[str, str], None]:
        """
        Subscribe to events for a specific game.

        Args:
            game_id: The game identifier

        Yields:
            Event dictionaries with 'event' and 'data' fields
        """
        # Create a new queue for this subscriber
        # Queue holds dict[str, str] to match SSEEvent.to_sse_format() return type
        queue: asyncio.Queue[dict[str, str]] = asyncio.Queue(maxsize=100)  # Limit queue size to prevent memory issues

        # Add to subscribers list
        self.subscribers[game_id].append(queue)

        try:
            # Initial connection event
            connected_event = SSEEvent.create_connected(game_id)
            yield connected_event.to_sse_format()

            # Continuously yield events from the queue
            while True:
                try:
                    # Wait for events with a timeout for heartbeat
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event_data
                except asyncio.exceptions.TimeoutError:
                    # Send heartbeat if no events for 30 seconds
                    heartbeat_event = SSEEvent.create_heartbeat()
                    yield heartbeat_event.to_sse_format()
                except Exception as e:
                    # Log unexpected errors and exit cleanly
                    logger.error(f"Error in SSE subscription for {game_id}: {e}")
                    break
        finally:
            # Clean up: remove this queue from subscribers
            if game_id in self.subscribers and queue in self.subscribers[game_id]:
                self.subscribers[game_id].remove(queue)
                if not self.subscribers[game_id]:
                    # No more subscribers for this game
                    self.subscribers.pop(game_id, None)
