"""Event manager for handling game events."""

from app.common.types import JSONSerializable
from app.interfaces.services import IEventManager
from app.models.game_state import GameEvent, GameEventType, GameState


class EventManager(IEventManager):
    """Manages game events following Single Responsibility Principle.

    Only handles event-related operations on game state.
    """

    def add_event(
        self,
        game_state: GameState,
        event_type: str,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game event to the history.

        Args:
            game_state: Game state to update
            event_type: Type of event (tool_call, tool_result, etc.)
            tool_name: Name of the tool that generated the event
            parameters: Tool parameters
            result: Tool result
            metadata: Additional metadata
        """
        game_state.add_game_event(
            event_type=GameEventType(event_type),
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            metadata=metadata,
        )

    def get_recent_events(self, game_state: GameState, limit: int = 50) -> list[GameEvent]:
        """Get recent game events.

        Args:
            game_state: Game state to read from
            limit: Maximum number of events to return

        Returns:
            List of recent events (most recent last)
        """
        if limit <= 0:
            return []

        return game_state.game_events[-limit:]

    def get_events_by_type(self, game_state: GameState, event_type: str) -> list[GameEvent]:
        """Get events of a specific type.

        Args:
            game_state: Game state to read from
            event_type: Type of events to retrieve

        Returns:
            List of matching events
        """
        target_type = GameEventType(event_type)
        return [event for event in game_state.game_events if event.event_type == target_type]
