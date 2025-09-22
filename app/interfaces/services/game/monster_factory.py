"""Interface for monster factory."""

from abc import ABC, abstractmethod

from app.models.instances.monster_instance import MonsterInstance
from app.models.monster import MonsterSheet


class IMonsterFactory(ABC):
    """Factory for creating MonsterInstance objects from templates."""

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
