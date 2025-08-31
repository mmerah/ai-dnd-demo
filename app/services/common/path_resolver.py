"""Path resolution service for consistent file access."""

from pathlib import Path

from app.interfaces.services import IPathResolver


class PathResolver(IPathResolver):
    """Service for resolving file paths across the application.

    Follows Single Responsibility Principle: only handles path resolution.
    """

    def __init__(self, root_dir: Path | None = None):
        """Initialize path resolver.

        Args:
            root_dir: Root directory of the project. Defaults to project root.
        """
        if root_dir is None:
            # Default to project root (3 levels up from this file)
            root_dir = Path(__file__).parent.parent.parent.parent
        self.root_dir = root_dir
        self.data_dir = self.root_dir / "data"
        self.saves_dir = self.root_dir / "saves"

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.saves_dir.mkdir(exist_ok=True)

    def get_data_dir(self) -> Path:
        """Get the root data directory."""
        return self.data_dir

    def get_saves_dir(self) -> Path:
        """Get the root saves directory."""
        return self.saves_dir

    def get_scenario_dir(self, scenario_id: str) -> Path:
        """Get directory for a specific scenario.

        Args:
            scenario_id: ID of the scenario

        Returns:
            Path to scenario directory
        """
        scenario_dir = self.data_dir / "scenarios" / scenario_id
        return scenario_dir

    def get_character_file(self, character_id: str) -> Path:
        """Get path to a character file.

        Args:
            character_id: ID of the character

        Returns:
            Path to character JSON file
        """
        return self.data_dir / "characters" / f"{character_id}.json"

    def get_save_dir(self, scenario_id: str, game_id: str) -> Path:
        """Get directory for a saved game.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            Path to save directory
        """
        save_dir = self.saves_dir / scenario_id / game_id
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    def resolve_scenario_component(self, scenario_id: str, component: str, item_id: str) -> Path:
        """Resolve path to a scenario component file.

        Args:
            scenario_id: ID of the scenario
            component: Component type (locations, npcs, quests, encounters)
            item_id: ID of the specific item

        Returns:
            Path to component JSON file
        """
        scenario_dir = self.get_scenario_dir(scenario_id)
        component_dir = scenario_dir / component
        return component_dir / f"{item_id}.json"

    def get_shared_data_file(self, data_type: str) -> Path:
        """Get path to a shared data file.

        Args:
            data_type: Type of data (items, spells, monsters)

        Returns:
            Path to shared data JSON file
        """
        return self.data_dir / f"{data_type}.json"
