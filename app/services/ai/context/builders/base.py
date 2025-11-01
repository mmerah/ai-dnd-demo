from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from app.interfaces.services.data import IRepository
from app.models.background import BackgroundDefinition
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.item import ItemDefinition
from app.models.spell import SpellDefinition


class DetailLevel(str, Enum):
    """Level of detail for context builders."""

    FULL = "full"
    SUMMARY = "summary"


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


class EntityContextBuilder(ABC):
    """Base class for builders that require a specific entity.

    Entity-aware builders operate on a specific character or NPC instance
    rather than deriving information from game state alone.
    """

    @abstractmethod
    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        """Build context for a specific entity.

        Args:
            game_state: Current game state
            context: Container with all required dependencies
            entity: The character or NPC instance to build context for

        Returns:
            Context string or None if not applicable
        """
        raise NotImplementedError
