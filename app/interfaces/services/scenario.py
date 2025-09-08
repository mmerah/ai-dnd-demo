from abc import ABC, abstractmethod

from app.models.monster import MonsterSheet
from app.models.npc import NPCSheet
from app.models.scenario import ScenarioSheet


class IScenarioService(ABC):
    """Interface for managing scenarios."""

    @abstractmethod
    def get_scenario(self, scenario_id: str) -> ScenarioSheet | None:
        pass

    @abstractmethod
    def list_scenarios(self) -> list[ScenarioSheet]:
        pass

    @abstractmethod
    def get_default_scenario(self) -> ScenarioSheet | None:
        pass

    @abstractmethod
    def get_scenario_context_for_ai(self, scenario: ScenarioSheet, current_location_id: str) -> str:
        pass

    @abstractmethod
    def get_scenario_npc(self, scenario_id: str, npc_id: str) -> NPCSheet | None:
        """Resolve a scenario NPC by id to an NPCSheet."""
        pass

    @abstractmethod
    def list_scenario_npcs(self, scenario_id: str) -> list[NPCSheet]:
        """List all NPCSheets defined in a scenario."""
        pass

    @abstractmethod
    def get_scenario_monster(self, scenario_id: str, monster_id: str) -> MonsterSheet | None:
        """Resolve a scenario-defined monster by id to a MonsterSheet."""
        pass
