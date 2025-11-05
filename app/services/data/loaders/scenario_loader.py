"""Loader for scenario data with modular components."""

import json
import logging
from pathlib import Path
from typing import Any

from app.interfaces.services.common import IPathResolver
from app.models.location import EncounterParticipantSpawn, LocationConnection, LootEntry
from app.models.npc import NPCSheet
from app.models.scenario import (
    Encounter,
    LocationDescriptions,
    ScenarioLocation,
    ScenarioMonster,
    ScenarioSheet,
    Secret,
)
from app.services.data.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class ScenarioLoader(BaseLoader[ScenarioSheet]):
    """Loader for scenario data with modular components."""

    def __init__(self, path_resolver: IPathResolver, validate_on_load: bool = True):
        """Initialize scenario loader.

        Args:
            path_resolver: Service for resolving file paths
            validate_on_load: Whether to validate data when loading
        """
        super().__init__(validate_on_load)
        self.path_resolver = path_resolver

    def _parse_data(self, data: dict[str, Any] | list[Any], source_path: Path) -> ScenarioSheet:
        if not isinstance(data, dict):
            raise RuntimeError(f"Expected dict for scenario data, got {type(data).__name__} from {source_path}")

        try:
            scenario_id = data.get("id", "default")
            scenario_dir = source_path.parent

            # Load all components
            npc_map = self._load_scenario_npcs(scenario_dir)
            monster_map = self._load_scenario_monsters(scenario_dir)
            encounter_map = self._load_scenario_encounters(scenario_dir)
            locations = self._load_locations(scenario_dir, data.get("locations", []), npc_map, monster_map)
            # Create the scenario
            scenario = ScenarioSheet(
                id=scenario_id,
                title=data.get("title", "Unknown Adventure"),
                description=data.get("description", ""),
                starting_location_id=data.get("starting_location_id", ""),
                locations=locations,
                encounters=encounter_map,
                random_encounters=[],  # TODO(MVP2): Load random encounters if needed
                content_packs=list(data.get("content_packs", ["srd"])),
            )

            if self.validate_on_load:
                self._validate_data(scenario)

            return scenario

        except Exception as e:
            raise RuntimeError(f"Failed to parse scenario from {source_path}: {e}") from e

    def _load_locations(
        self,
        scenario_dir: Path,
        location_ids: list[str],
        npc_map: dict[str, NPCSheet],
        monster_map: dict[str, Any],
    ) -> list[ScenarioLocation]:
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
                    location = self._load_location_file(location_file, npc_map, monster_map)
                    locations.append(location)
                except Exception as e:
                    logger.warning(f"Failed to load location {location_id}: {e}")

        return locations

    def _load_location_file(
        self, file_path: Path, npc_map: dict[str, NPCSheet], monster_map: dict[str, Any]
    ) -> ScenarioLocation:
        """Load a single location from file.

        Args:
            file_path: Path to location JSON file

        Returns:
            Loaded ScenarioLocation
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Parse notable monsters by ids (optional per-location)
        notable_monsters = []
        monster_ids = data.get("monster_ids")
        if isinstance(monster_ids, list) and monster_ids:
            for mid in monster_ids:
                sm = monster_map.get(str(mid))
                if sm:
                    notable_monsters.append(sm)

        # Parse encounter_ids (normalized approach)
        encounter_ids: list[str] = []
        raw_encounter_ids = data.get("encounter_ids")
        if isinstance(raw_encounter_ids, list):
            for eid in raw_encounter_ids:
                if isinstance(eid, str):
                    encounter_ids.append(eid)

        # Parse monster_ids as list of strings for the model
        # (different from the notable_monsters loaded above)
        location_monster_ids: list[str] = []
        raw_monster_ids = data.get("monster_ids")
        if isinstance(raw_monster_ids, list):
            for mid in raw_monster_ids:
                if isinstance(mid, str):
                    location_monster_ids.append(mid)

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
            notable_monsters=notable_monsters,
            encounter_ids=encounter_ids,
            monster_ids=location_monster_ids,
            connections=connections,
            events=data.get("events", []),
            environmental_features=data.get("environmental_features", []),
            secrets=secrets,
            loot_table=loot_table,
            victory_conditions=data.get("victory_conditions", []),
            danger_level=data.get("danger_level", "moderate"),
        )

    def _load_scenario_npcs(self, scenario_dir: Path) -> dict[str, NPCSheet]:
        """Load all scenario NPC files into a map by id."""
        npcs_dir = scenario_dir / "npcs"
        npc_map: dict[str, NPCSheet] = {}
        if not npcs_dir.exists():
            return npc_map
        for file_path in npcs_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    raw = json.load(f)
                npc = NPCSheet(**raw)
                npc_map[npc.id] = npc
            except Exception as e:
                logger.warning(f"Failed to load scenario NPC from {file_path}: {e}")
        return npc_map

    def _load_scenario_monsters(self, scenario_dir: Path) -> dict[str, Any]:
        """Load all scenario notable monsters into a map by id."""
        monsters_dir = scenario_dir / "monsters"
        m_map: dict[str, ScenarioMonster] = {}
        if not monsters_dir.exists():
            return m_map

        # Extract scenario ID from directory path
        # scenario_dir is like data/scenarios/goblin-cave-adventure/
        scenario_id = scenario_dir.name

        for file_path in monsters_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    raw = json.load(f)

                # Parse skills from dict to list format if needed
                if "monster" in raw and "skills" in raw["monster"]:
                    skills_data = raw["monster"]["skills"]
                    if isinstance(skills_data, dict):
                        # Convert dict format to list of SkillValue
                        skills_list = []
                        for skill_name, modifier in skills_data.items():
                            # Normalize skill name to index format
                            skill_index = skill_name.lower().replace(" ", "-")
                            skills_list.append({"index": skill_index, "value": modifier})
                        raw["monster"]["skills"] = skills_list

                # Inject content_pack field for scenario-specific monsters
                if "monster" in raw:
                    raw["monster"]["content_pack"] = f"scenario:{scenario_id}"

                sm = ScenarioMonster(**raw)
                m_map[sm.id] = sm
            except Exception as e:
                logger.warning(f"Failed to load scenario monster from {file_path}: {e}")
        return m_map

    def _parse_participant_spawns(self, data: dict[str, Any]) -> list[EncounterParticipantSpawn]:
        """Parse participant spawns from encounter JSON with backward compatibility.

        Requires the 'participant_spawns' key. Raises ValueError on invalid
        entries to fail fast during load/validation.
        """
        spawns: list[EncounterParticipantSpawn] = []
        if "participant_spawns" not in data:
            raise ValueError("Encounter must define 'participant_spawns'")
        raw_list = data.get("participant_spawns")
        if not isinstance(raw_list, list):
            raise ValueError("participant_spawns must be a list")
        for idx, spawn_data in enumerate(raw_list):
            if not isinstance(spawn_data, dict):
                raise ValueError(f"Invalid spawn entry at index {idx}: expected object")
            try:
                spawns.append(EncounterParticipantSpawn(**spawn_data))
            except Exception as e:
                raise ValueError(f"Invalid participant spawn at index {idx}: {e}") from e
        return spawns

    def _load_scenario_encounters(self, scenario_dir: Path) -> dict[str, Encounter]:
        """Load all scenario encounters into a map by id."""
        encounters_dir = scenario_dir / "encounters"
        encounter_map: dict[str, Encounter] = {}
        if not encounters_dir.exists():
            return encounter_map

        for file_path in encounters_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                participant_spawns = self._parse_participant_spawns(data)

                encounter = Encounter(
                    id=data["id"],
                    type=data.get("type", "combat"),
                    description=data.get("description", ""),
                    difficulty=data.get("difficulty"),
                    participant_spawns=participant_spawns,
                    dc=data.get("dc"),
                    rewards=data.get("rewards", []),
                )
                encounter_map[encounter.id] = encounter
            except Exception as e:
                logger.warning(f"Failed to load encounter from {file_path}: {e}")

        return encounter_map
