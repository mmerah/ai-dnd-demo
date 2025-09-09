"""Event manager for handling game events."""

from app.common.types import JSONSerializable
from app.interfaces.services.game import IEventManager
from app.models.game_state import GameEvent, GameEventType, GameState


class EventManager(IEventManager):
    """Manages game events following Single Responsibility Principle.

    Only handles event-related operations on game state.
    """

    def add_event(
        self,
        game_state: GameState,
        event_type: GameEventType,
        tool_name: str,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game event to the history.

        Args:
            game_state: Game state to update
            event_type: Type of event (GameEventType enum)
            tool_name: Name of the tool that generated the event
            parameters: Tool parameters (default: empty dict)
            result: Tool result (default: empty dict)
        """
        event = GameEvent(
            event_type=event_type,
            tool_name=tool_name,
            parameters=parameters or {},
            result=result or {},
        )
        game_state.add_game_event(event)
