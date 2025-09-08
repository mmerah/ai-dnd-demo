from abc import ABC, abstractmethod

from app.models.game_state import GameState


class ContextBuilder(ABC):
    @abstractmethod
    def build(self, game_state: GameState) -> str | None:
        """Build a specific part of the AI context string."""
        raise NotImplementedError
