"""Event manager for handling game events."""

from app.common.types import JSONSerializable
from app.interfaces.services.game import IEventManager
from app.models.game_state import GameEvent, GameEventType, GameState


class EventManager(IEventManager):
    """Manages game events"""

    def add_event(
        self,
        game_state: GameState,
        event_type: GameEventType,
        tool_name: str,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
    ) -> None:
        event = GameEvent(
            event_type=event_type,
            tool_name=tool_name,
            parameters=parameters or {},
            result=result or {},
        )
        game_state.game_events.append(event)
