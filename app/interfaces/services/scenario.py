from abc import ABC, abstractmethod

from app.models.monster import MonsterSheet
from app.models.npc import NPCSheet
from app.models.scenario import ScenarioSheet


class IScenarioService(ABC):
    """Interface for managing scenarios."""

    @abstractmethod
    def get_scenario(self, scenario_id: str) -> ScenarioSheet | None:
        """Get a scenario by ID.

        Args:
            scenario_id: ID of the scenario to retrieve

        Returns:
            ScenarioSheet if found, None otherwise
        """
        pass

    @abstractmethod
    def list_scenarios(self) -> list[ScenarioSheet]:
        """List all available scenarios.

        Returns:
            List of all ScenarioSheet objects
        """
        pass

    @abstractmethod
    def get_scenario_npc(self, scenario_id: str, npc_id: str) -> NPCSheet | None:
        """Get a scenario-specific NPC by ID.

        Args:
            scenario_id: ID of the scenario
            npc_id: ID of the NPC within the scenario

        Returns:
            NPCSheet if found, None otherwise
        """
        pass

    @abstractmethod
    def list_scenario_npcs(self, scenario_id: str) -> list[NPCSheet]:
        """List all NPCs defined in a scenario.

        Args:
            scenario_id: ID of the scenario

        Returns:
            List of NPCSheet objects for the scenario
        """
        pass

    @abstractmethod
    def get_scenario_monster(self, scenario_id: str, monster_id: str) -> MonsterSheet | None:
        """Get a scenario-specific monster by ID.

        Args:
            scenario_id: ID of the scenario
            monster_id: ID of the monster within the scenario

        Returns:
            MonsterSheet if found, None otherwise
        """
        pass
