"""Interface for monster manager service."""

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.instances.monster_instance import MonsterInstance
from app.models.monster import MonsterSheet


class IMonsterManagerService(ABC):
    """Service for managing monster instances."""

    @abstractmethod
    def create(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        """Create a MonsterInstance from a MonsterSheet template.

        Initializes entity state with computed values based on monster stats.

        Args:
            sheet: Monster template with base stats
            current_location_id: ID of spawn location

        Returns:
            MonsterInstance with initialized EntityState
        """
        pass

    @abstractmethod
    def add_monster_to_game(self, game_state: GameState, monster: MonsterInstance) -> str:
        """Add a MonsterInstance to the game state with name deduplication.

        Ensures unique display names by appending suffixes if needed.
        Mutates the monster's sheet.name if deduplication occurs.

        Args:
            game_state: The game state to add the monster to
            monster: The monster instance to add

        Returns:
            Final display name (with suffix if deduped)
        """
        pass
