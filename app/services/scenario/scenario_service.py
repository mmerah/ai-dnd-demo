"""Service for managing scenarios."""

from app.interfaces.services import ILoader, IMonsterRepository, IPathResolver, IScenarioService
from app.models.scenario import Scenario


class ScenarioService(IScenarioService):
    """Service for loading and managing scenarios."""

    def __init__(
        self,
        path_resolver: IPathResolver,
        scenario_loader: ILoader[Scenario],
        monster_repository: IMonsterRepository,
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
        self._scenarios: dict[str, Scenario] = {}
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
                            print(f"Failed to load scenario {scenario_id}: {e}")
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
                print(f"Failed to load legacy scenario: {e}")

    def get_scenario(self, scenario_id: str) -> Scenario | None:
        """
        Get a scenario by ID.

        Args:
            scenario_id: ID of the scenario to retrieve

        Returns:
            Scenario object or None if not found
        """
        return self._scenarios.get(scenario_id)

    def list_scenarios(self) -> list[Scenario]:
        """
        List all available scenarios.

        Returns:
            List of Scenario objects
        """
        return list(self._scenarios.values())

    def get_default_scenario(self) -> Scenario | None:
        """
        Get the default scenario (first available).

        Returns:
            First available Scenario or None if no scenarios loaded
        """
        if self._scenarios:
            # Prefer goblin-cave-adventure if available
            if "goblin-cave-adventure" in self._scenarios:
                return self._scenarios["goblin-cave-adventure"]
            # Otherwise return the first scenario
            return next(iter(self._scenarios.values()))
        return None

    def get_scenario_context_for_ai(self, scenario: Scenario, current_location_id: str) -> str:
        """
        Get scenario context string for AI.

        Args:
            scenario: The scenario
            current_location_id: Current location ID

        Returns:
            Context string for AI
        """
        context = f"# {scenario.title}\n\n{scenario.description}\n\n"

        # Add current location context if available
        location = scenario.get_location(current_location_id)
        if location:
            context += f"## Current Location: {location.name}\n{location.description}\n\n"

            if location.npcs:
                context += "NPCs present:\n"
                for npc in location.npcs:
                    context += f"- {npc.name} ({npc.role}): {npc.description}\n"
                context += "\n"

            if location.encounters:
                context += f"Potential encounters: {len(location.encounters)} available\n\n"

        return context
