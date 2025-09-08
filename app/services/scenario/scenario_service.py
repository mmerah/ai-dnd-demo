"""Service for managing scenarios."""

import json
import logging

from app.interfaces.services.character import ICharacterService
from app.interfaces.services.common import IPathResolver
from app.interfaces.services.data import ILoader, IMonsterRepository
from app.interfaces.services.scenario import IScenarioService
from app.models.monster import MonsterSheet
from app.models.npc import NPCSheet
from app.models.scenario import ScenarioMonster, ScenarioSheet

logger = logging.getLogger(__name__)


class ScenarioService(IScenarioService):
    """Service for loading and managing scenarios."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        scenario_loader: ILoader[ScenarioSheet],
        monster_repository: IMonsterRepository,
        character_service: ICharacterService,
    ):
        """
        Initialize scenario service.

        Args:
            path_resolver: Service for resolving file paths
            scenario_loader: Loader for scenario data
            monster_repository: Repository for validating monster references
        """
        self.path_resolver = path_resolver
        self.scenario_loader = scenario_loader
        self.monster_repository = monster_repository
        self.character_service = character_service
        self._scenarios: dict[str, ScenarioSheet] = {}
        self._load_all_scenarios()

    def _load_all_scenarios(self) -> None:
        """Load all available scenarios from data directory."""
        # Check for scenarios directory with modular structure
        scenarios_dir = self.path_resolver.get_data_dir() / "scenarios"
        if scenarios_dir.exists() and scenarios_dir.is_dir():
            for scenario_dir in scenarios_dir.iterdir():
                if scenario_dir.is_dir():
                    scenario_id = scenario_dir.name
                    # Use the generic load method with the scenario.json file path
                    scenario_file = scenario_dir / "scenario.json"
                    if scenario_file.exists():
                        try:
                            scenario = self.scenario_loader.load(scenario_file)
                        except Exception as e:
                            logger.error(f"Failed to load scenario {scenario_id}: {e}")
                            scenario = None
                    else:
                        scenario = None
                    if scenario:
                        self._scenarios[scenario.id] = scenario

        # Also check for legacy single scenario.json file
        scenario_path = self.path_resolver.get_data_dir() / "scenario.json"
        if scenario_path.exists():
            try:
                scenario = self.scenario_loader.load(scenario_path)
                if scenario:
                    self._scenarios[scenario.id] = scenario
            except Exception as e:
                logger.error(f"Failed to load legacy scenario: {e}")

    def get_scenario(self, scenario_id: str) -> ScenarioSheet | None:
        """
        Get a scenario by ID.

        Args:
            scenario_id: ID of the scenario to retrieve

        Returns:
            Scenario object or None if not found
        """
        return self._scenarios.get(scenario_id)

    def list_scenarios(self) -> list[ScenarioSheet]:
        """
        List all available scenarios.

        Returns:
            List of Scenario objects
        """
        return list(self._scenarios.values())

    def get_scenario_npc(self, scenario_id: str, npc_id: str) -> NPCSheet | None:
        """Load a specific scenario NPC by id from disk.

        This avoids duplicating data in memory and keeps scenario NPCs normalized.
        """
        try:
            npc_path = self.path_resolver.get_scenario_dir(scenario_id) / "npcs" / f"{npc_id}.json"
            if not npc_path.exists():
                return None
            import json

            with open(npc_path, encoding="utf-8") as f:
                data = json.load(f)
            npc = NPCSheet(**data)

            # Validate NPC character sheet if character service available (fail-fast)
            errors = self.character_service.validate_character_references(npc.character)
            if errors:
                raise ValueError(f"NPC {npc.id} has invalid references: {', '.join(errors)}")

            return npc
        except Exception as e:
            logger.error(f"Failed to load NPC {npc_id} from scenario {scenario_id}: {e}")
            raise

    def get_scenario_monster(self, scenario_id: str, monster_id: str) -> MonsterSheet | None:
        """Load a scenario-defined monster by id and return its MonsterSheet model.

        Returns None if not found or invalid.
        """
        try:
            m_path = self.path_resolver.get_scenario_dir(scenario_id) / "monsters" / f"{monster_id}.json"
            if not m_path.exists():
                return None
            with open(m_path, encoding="utf-8") as f:
                data = json.load(f)
            sm = ScenarioMonster(**data)
            return sm.monster
        except Exception:
            return None

    def list_scenario_npcs(self, scenario_id: str) -> list[NPCSheet]:
        """List all NPCSheets defined in a scenario."""
        npcs: list[NPCSheet] = []
        try:
            npcs_dir = self.path_resolver.get_scenario_dir(scenario_id) / "npcs"
            if not npcs_dir.exists():
                return npcs

            for npc_file in npcs_dir.glob("*.json"):
                try:
                    with open(npc_file, encoding="utf-8") as f:
                        data = json.load(f)
                    npc = NPCSheet(**data)

                    # Validate NPC character sheet if character service available (fail-fast)
                    errors = self.character_service.validate_character_references(npc.character)
                    if errors:
                        logger.warning(f"NPC {npc.id} has invalid references: {', '.join(errors)}")
                        continue

                    npcs.append(npc)
                except Exception as e:
                    logger.warning(f"Failed to load NPC from {npc_file}: {e}")
                    continue

            return npcs
        except Exception as e:
            logger.error(f"Failed to list NPCs for scenario {scenario_id}: {e}")
            return []
