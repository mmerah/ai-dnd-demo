from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.interfaces.services.data import IRepository
from app.models.background import BackgroundDefinition
from app.models.game_state import GameState
from app.models.item import ItemDefinition
from app.models.spell import SpellDefinition


@dataclass
class BuildContext:
    """Type-safe container for all context builder dependencies."""

    item_repository: IRepository[ItemDefinition]
    spell_repository: IRepository[SpellDefinition]
    background_repository: IRepository[BackgroundDefinition]


class ContextBuilder(ABC):
    @abstractmethod
    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        """Build a specific part of the AI context string.

        Args:
            game_state: Current game state
            context: Container with all required dependencies

        Returns:
            Context string or None if not applicable
        """
        raise NotImplementedError
