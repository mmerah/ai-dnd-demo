"""
Broadcast service for pub/sub SSE event streaming.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class SSEEvent(TypedDict):
    """Structure of an SSE event."""

    event: str
    data: Any  # Can be various types depending on the event
    timestamp: str


class BroadcastService:
    """Service for broadcasting SSE events to connected clients."""

    def __init__(self) -> None:
        """Initialize the broadcast service with empty queues."""
        # Dictionary of game_id -> list of subscriber queues
        self.subscribers: dict[str, list[asyncio.Queue[SSEEvent]]] = defaultdict(list)

    async def publish(self, game_id: str, event: str, data: Any) -> None:
        """
        Publish an event to all subscribers for a specific game.

        Args:
            game_id: The game identifier
            event: The event type (e.g., 'narrative', 'tool_result')
            data: The event data (will be JSON-serialized)
        """
        # Get all subscriber queues for this game
        queues = self.subscribers.get(game_id, [])
        # Log all events for debugging
        logger.info(f"Publishing event '{event}' to {len(queues)} subscribers for game {game_id}")
        if event in ["tool_call", "tool_result"]:
            logger.info(f"Tool event data: {data}")

        # Remove dead queues (full or closed)
        active_queues = []
        for queue in queues:
            try:
                # Try to put the event in the queue (non-blocking check first)
                sse_event: SSEEvent = {"event": event, "data": data, "timestamp": datetime.now(UTC).isoformat()}
                queue.put_nowait(sse_event)
                active_queues.append(queue)
            except (asyncio.QueueFull, Exception):
                # Queue is full or closed, skip it
                pass

        # Update the subscriber list with only active queues
        if active_queues:
            self.subscribers[game_id] = active_queues
        else:
            # No active subscribers, remove the game entry
            self.subscribers.pop(game_id, None)

    async def subscribe(self, game_id: str) -> AsyncGenerator[SSEEvent, None]:
        """
        Subscribe to events for a specific game.

        Args:
            game_id: The game identifier

        Yields:
            Event dictionaries with 'event' and 'data' fields
        """
        # Create a new queue for this subscriber
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=100)  # Limit queue size to prevent memory issues

        # Add to subscribers list
        self.subscribers[game_id].append(queue)

        try:
            # Initial connection event
            yield {
                "event": "connected",
                "data": {"game_id": game_id, "status": "connected"},
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Continuously yield events from the queue
            while True:
                try:
                    # Wait for events with a timeout for heartbeat
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event_data
                except TimeoutError:
                    # Send heartbeat if no events for 30 seconds
                    yield {"event": "heartbeat", "data": {}, "timestamp": datetime.now(UTC).isoformat()}
        finally:
            # Clean up: remove this queue from subscribers
            if game_id in self.subscribers and queue in self.subscribers[game_id]:
                self.subscribers[game_id].remove(queue)
                if not self.subscribers[game_id]:
                    # No more subscribers for this game
                    self.subscribers.pop(game_id, None)

    def get_subscriber_count(self, game_id: str) -> int:
        """Get the number of active subscribers for a game."""
        return len(self.subscribers.get(game_id, []))

    def get_all_games_with_subscribers(self) -> list[str]:
        """Get list of all game IDs that have active subscribers."""
        return list(self.subscribers.keys())


# Create singleton instance
broadcast_service = BroadcastService()
