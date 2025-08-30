"""Service for managing scenarios."""

import json
from pathlib import Path

from app.interfaces.services import IDataService, IScenarioService
from app.models.scenario import Scenario


class ScenarioService(IScenarioService):
    """Service for loading and managing scenarios."""

    def __init__(self, data_service: IDataService | None = None, data_directory: Path | None = None):
        """
        Initialize scenario service.

        Args:
            data_service: Data service for validating references (optional, validation skipped if None)
            data_directory: Path to data directory containing scenarios
        """
        if data_directory is None:
            # Default to app/data directory
            data_directory = Path(__file__).parent.parent / "data"
        self.data_directory = data_directory
        self.data_service = data_service
        self._scenarios: dict[str, Scenario] = {}
        self._load_all_scenarios()

    def _load_all_scenarios(self) -> None:
        """Load all available scenarios from data directory."""
        # Load the main scenario.json
        scenario_path = self.data_directory / "scenario.json"
        if scenario_path.exists():
            scenario = self.load_scenario_from_file(scenario_path)
            if scenario:
                self._scenarios[scenario.id] = scenario

        # Also check for a scenarios directory with multiple scenarios
        scenarios_dir = self.data_directory / "scenarios"
        if scenarios_dir.exists() and scenarios_dir.is_dir():
            for scenario_file in scenarios_dir.glob("*.json"):
                scenario = self.load_scenario_from_file(scenario_file)
                if scenario:
                    self._scenarios[scenario.id] = scenario

    def load_scenario_from_file(self, file_path: Path) -> Scenario | None:
        """
        Load a scenario from a JSON file.

        Args:
            file_path: Path to scenario JSON file

        Returns:
            Loaded Scenario object or None if failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Add ID based on filename if not present
            if "id" not in data:
                data["id"] = file_path.stem

            scenario = Scenario(**data)

            # Validate references if data service is available
            if self.data_service:
                errors = self.validate_scenario_references(scenario, self.data_service)
                if errors:
                    error_msg = f"Scenario '{scenario.id}' has invalid references:\n"
                    for error in errors:
                        error_msg += f"  - {error}\n"
                    raise ValueError(error_msg)

            return scenario
        except (ValueError, TypeError):
            # Re-raise validation and type errors (fail fast)
            raise
        except Exception as e:
            # Only catch truly unexpected errors (file IO, JSON parsing)
            print(f"Failed to load scenario from {file_path}: {e}")
            return None

    def get_scenario(self, scenario_id: str = "scenario") -> Scenario | None:
        """
        Get a scenario by ID.

        Args:
            scenario_id: ID of the scenario to retrieve

        Returns:
            Scenario object or None if not found
        """
        return self._scenarios.get(scenario_id)

    def get_default_scenario(self) -> Scenario | None:
        """
        Get the default scenario.

        Returns:
            Default scenario or first available scenario
        """
        # Try to get the main scenario.json first
        if "scenario" in self._scenarios:
            return self._scenarios["scenario"]

        # Otherwise return the first available scenario
        if self._scenarios:
            return next(iter(self._scenarios.values()))

        return None

    def list_scenarios(self) -> list[Scenario]:
        """
        List all available scenarios.

        Returns:
            List of Scenario objects
        """
        return list(self._scenarios.values())

    def get_scenario_context_for_ai(self, scenario: Scenario, current_location_id: str) -> str:
        """
        Generate scenario context for AI.

        Args:
            scenario: The scenario object
            current_location_id: Current location ID

        Returns:
            Context string for AI
        """
        context_parts = []

        # Add scenario overview
        context_parts.append(f"Scenario: {scenario.title}")
        context_parts.append(f"Description: {scenario.description}")

        # Add current location details
        location = scenario.get_location(current_location_id)
        if location:
            context_parts.append(f"\nCurrent Location: {location.name}")
            context_parts.append(f"Description: {location.description}")

            if location.npcs:
                npc_list = ", ".join([npc.name for npc in location.npcs])
                context_parts.append(f"NPCs present: {npc_list}")

            if location.environmental_features:
                context_parts.append(f"Environmental features: {', '.join(location.environmental_features)}")

            if location.connections:
                connected_locations = []
                for conn in location.connections:
                    conn_loc = scenario.get_location(conn.to_location_id)
                    if conn_loc:
                        connected_locations.append(conn_loc.name)
                if connected_locations:
                    context_parts.append(f"Connected locations: {', '.join(connected_locations)}")

        # Add current act/progression info
        for i, act in enumerate(scenario.progression.acts):
            if current_location_id in act.locations:
                context_parts.append(f"\nCurrent Act: Act {i + 1} - {act.name}")
                context_parts.append(f"Act Objectives: {', '.join(act.objectives)}")
                break

        return "\n".join(context_parts)

    def validate_scenario_references(self, scenario: Scenario, data_service: IDataService) -> list[str]:
        """
        Validate all monster and item references in a scenario. Checks that all referenced monsters and
        items in the scenario actually exist in the data service.

        Args:
            scenario: The scenario to validate
            data_service: The data service to check references against

        Returns:
            List of validation error messages
        """
        errors = []

        # Check all monster references
        for location in scenario.locations:
            for encounter in location.encounters:
                for spawn in encounter.monster_spawns:
                    if not data_service.validate_monster_reference(spawn.monster_name):
                        errors.append(
                            f"Location '{location.name}': Monster '{spawn.monster_name}' not found in database",
                        )

            # Check loot references
            for loot in location.loot_table:
                if not data_service.validate_item_reference(loot.item_name):
                    errors.append(f"Location '{location.name}': Item '{loot.item_name}' not found in database")

            # Check NPC valuable items
            for npc in location.npcs:
                if npc.valuable_item and not data_service.validate_item_reference(npc.valuable_item):
                    errors.append(f"NPC '{npc.name}': Item '{npc.valuable_item}' not found in database")

        return errors
