"""Interface for event manager."""

from abc import ABC, abstractmethod

from app.common.types import JSONSerializable
from app.models.game_state import GameEventType, GameState


class IEventManager(ABC):
    """Interface for managing game events."""

    @abstractmethod
    def add_event(
        self,
        game_state: GameState,
        event_type: GameEventType,
        tool_name: str,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game event.

        Args:
            game_state: Game state to update
            event_type: Type of event (GameEventType enum)
            tool_name: Tool that generated the event
            parameters: Event parameters
            result: Event result
        """
        pass
