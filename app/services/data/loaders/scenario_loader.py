"""Loader for scenario data with modular components."""

import json
import logging
from pathlib import Path
from typing import Any

from app.interfaces.services import IPathResolver
from app.models.location import LocationConnection, LootEntry, MonsterSpawn
from app.models.quest import ObjectiveStatus, Quest, QuestObjective, QuestStatus
from app.models.scenario import (
    Encounter,
    LocationDescriptions,
    Scenario,
    ScenarioAct,
    ScenarioLocation,
    ScenarioNPC,
    ScenarioProgression,
    Secret,
    TreasureGuidelines,
)
from app.services.data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class ScenarioLoader(BaseLoader[Scenario]):
    """Loader for scenario data with modular components.

    Follows Single Responsibility Principle: only handles scenario file operations.
    Loads scenario metadata and all associated components from the modular structure.
    """

    def __init__(self, path_resolver: IPathResolver, validate_on_load: bool = True):
        """Initialize scenario loader.

        Args:
            path_resolver: Service for resolving file paths
            validate_on_load: Whether to validate data when loading
        """
        super().__init__(validate_on_load)
        self.path_resolver = path_resolver

    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> Scenario:
        # Any is necessary because raw JSON data can contain mixed types
        """Parse raw JSON data into Scenario model.

        This method loads the scenario metadata and then loads all
        components from their respective directories.

        Args:
            data: Raw JSON data from scenario.json
            source_path: Path the data was loaded from

        Returns:
            Fully loaded Scenario with all components

        Raises:
            RuntimeError: If parsing fails
        """
        if not isinstance(data, dict):
            raise RuntimeError(f"Expected dict for scenario data, got {type(data).__name__} from {source_path}")

        try:
            scenario_id = data.get("id", "default")
            scenario_dir = source_path.parent

            # Load all components
            locations = self._load_locations(scenario_dir, data.get("locations", []))
            quests = self._load_quests(scenario_dir, data.get("quests", []))
            progression = self._load_progression(scenario_dir, data.get("progression", "acts"))
            treasure_guidelines = self._parse_treasure_guidelines(data.get("treasure_guidelines", {}))

            # Create the scenario
            scenario = Scenario(
                id=scenario_id,
                title=data.get("title", "Unknown Adventure"),
                description=data.get("description", ""),
                starting_location=data.get("starting_location", ""),
                locations=locations,
                quests=quests,
                progression=progression if progression else ScenarioProgression(acts=[]),
                random_encounters=[],  # TODO: Load random encounters if needed
                treasure_guidelines=treasure_guidelines,
            )

            if self.validate_on_load:
                self._validate_data(scenario)

            return scenario

        except Exception as e:
            raise RuntimeError(f"Failed to parse scenario from {source_path}: {e}") from e

    def _load_locations(self, scenario_dir: Path, location_ids: list[str]) -> list[ScenarioLocation]:
        """Load all location files for the scenario.

        Args:
            scenario_dir: Directory containing the scenario
            location_ids: List of location IDs to load

        Returns:
            List of loaded ScenarioLocation objects
        """
        locations: list[ScenarioLocation] = []
        locations_dir = scenario_dir / "locations"

        if not locations_dir.exists():
            return locations

        for location_id in location_ids:
            location_file = locations_dir / f"{location_id}.json"
            if location_file.exists():
                try:
                    location = self._load_location_file(location_file)
                    locations.append(location)
                except Exception as e:
                    logger.warning(f"Failed to load location {location_id}: {e}")

        return locations

    def _load_location_file(self, file_path: Path) -> ScenarioLocation:
        """Load a single location from file.

        Args:
            file_path: Path to location JSON file

        Returns:
            Loaded ScenarioLocation
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Parse NPCs
        npcs = []
        for npc_data in data.get("npcs", []):
            npcs.append(ScenarioNPC(**npc_data))

        # Parse encounters
        encounters = []
        for enc_data in data.get("encounters", []):
            monster_spawns = []
            for spawn_data in enc_data.get("monster_spawns", []):
                monster_spawns.append(MonsterSpawn(**spawn_data))

            encounters.append(
                Encounter(
                    id=enc_data.get("id"),
                    type=enc_data.get("type"),
                    description=enc_data.get("description"),
                    difficulty=enc_data.get("difficulty"),
                    monster_spawns=monster_spawns,
                    dc=enc_data.get("dc"),
                    rewards=enc_data.get("rewards", []),
                )
            )

        # Parse connections
        connections = []
        for conn_data in data.get("connections", []):
            connections.append(LocationConnection(**conn_data))

        # Parse secrets
        secrets = []
        for secret_data in data.get("secrets", []):
            secrets.append(Secret(**secret_data))

        # Parse loot table
        loot_table = []
        for loot_data in data.get("loot_table", []):
            loot_table.append(LootEntry(**loot_data))

        # Parse descriptions
        descriptions = None
        if "descriptions" in data:
            desc_data = data["descriptions"]
            descriptions = LocationDescriptions(
                first_visit=desc_data.get("first_visit", ""),
                return_visit=desc_data.get("return_visit"),
                cleared=desc_data.get("cleared"),
                special_conditions=desc_data.get("special_conditions", {}),
            )

        return ScenarioLocation(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            descriptions=descriptions,
            npcs=npcs,
            encounters=encounters,
            connections=connections,
            events=data.get("events", []),
            environmental_features=data.get("environmental_features", []),
            secrets=secrets,
            loot_table=loot_table,
            victory_conditions=data.get("victory_conditions", []),
            danger_level=data.get("danger_level", "moderate"),
        )

    def _load_quests(self, scenario_dir: Path, quest_ids: list[str]) -> list[Quest]:
        """Load all quest files for the scenario.

        Args:
            scenario_dir: Directory containing the scenario
            quest_ids: List of quest IDs to load

        Returns:
            List of loaded Quest objects
        """
        quests: list[Quest] = []
        quests_dir = scenario_dir / "quests"

        if not quests_dir.exists():
            return quests

        for quest_id in quest_ids:
            quest_file = quests_dir / f"{quest_id}.json"
            if quest_file.exists():
                try:
                    quest = self._load_quest_file(quest_file)
                    quests.append(quest)
                except Exception as e:
                    logger.warning(f"Failed to load quest {quest_id}: {e}")

        return quests

    def _load_quest_file(self, file_path: Path) -> Quest:
        """Load a single quest from file.

        Args:
            file_path: Path to quest JSON file

        Returns:
            Loaded Quest
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Parse objectives
        objectives = []
        for obj_data in data.get("objectives", []):
            objectives.append(
                QuestObjective(
                    id=obj_data["id"],
                    description=obj_data["description"],
                    status=ObjectiveStatus(obj_data.get("status", "pending")),
                    required=obj_data.get("required", True),
                    metadata=obj_data.get("metadata", {}),
                )
            )

        return Quest(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            objectives=objectives,
            status=QuestStatus(data.get("status", "not_started")),
            rewards_description=data.get("rewards_description", ""),
            prerequisites=data.get("prerequisites", []),
            act=data.get("act"),
        )

    def _load_progression(self, scenario_dir: Path, progression_type: str) -> ScenarioProgression | None:
        """Load scenario progression (acts).

        Args:
            scenario_dir: Directory containing the scenario
            progression_type: Type of progression (currently only "acts")

        Returns:
            Loaded ScenarioProgression or None
        """
        if progression_type != "acts":
            return None

        progression_dir = scenario_dir / "progression"
        acts_file = progression_dir / "acts.json"

        if not acts_file.exists():
            return None

        try:
            with open(acts_file, encoding="utf-8") as f:
                data = json.load(f)

            acts = []
            for act_data in data.get("acts", []):
                acts.append(
                    ScenarioAct(
                        id=act_data["id"],
                        name=act_data["name"],
                        locations=act_data.get("locations", []),
                        objectives=act_data.get("objectives", []),
                        quests=act_data.get("quests", []),
                        completion_requirements=act_data.get("completion_requirements", []),
                    )
                )

            return ScenarioProgression(
                acts=acts,
                current_act_index=data.get("current_act_index", 0),
            )

        except Exception as e:
            logger.warning(f"Failed to load progression: {e}")
            return None

    def _parse_treasure_guidelines(self, data: dict[str, Any]) -> TreasureGuidelines:
        # Any is necessary because treasure data from JSON can contain mixed types
        """Parse treasure guidelines from data.

        Args:
            data: Raw treasure guidelines data

        Returns:
            TreasureGuidelines object
        """
        return TreasureGuidelines(
            total_gold=data.get("total_gold", ""),
            magic_items=data.get("magic_items", ""),
            consumables=data.get("consumables", ""),
            mundane_items=data.get("mundane_items", ""),
        )

    def _prepare_for_save(self, data: Scenario) -> dict[str, Any]:
        # Any is necessary for JSON-serializable output
        """Prepare scenario data for JSON serialization.

        Args:
            data: Scenario to save

        Returns:
            JSON-serializable dictionary
        """
        # For scenarios, we would need to split the data back into components
        # This is complex and might not be needed for the MVP
        return data.model_dump(mode="json")

    def load_scenario(self, scenario_id: str) -> Scenario | None:
        """Load a complete scenario by ID.

        Args:
            scenario_id: ID of the scenario to load

        Returns:
            Loaded Scenario or None if not found
        """
        scenario_dir = self.path_resolver.get_scenario_dir(scenario_id)
        scenario_file = scenario_dir / "scenario.json"

        if not scenario_file.exists():
            return None

        try:
            return self.load(scenario_file)
        except Exception as e:
            logger.error(f"Failed to load scenario {scenario_id}: {e}")
            return None
