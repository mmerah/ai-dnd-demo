"""Path resolution service for consistent file access."""

import re
from pathlib import Path

from app.interfaces.services.common import IPathResolver


class PathResolver(IPathResolver):
    """Service for resolving file paths across the application."""

    # Pattern for valid IDs - only alphanumeric, hyphens, and underscores
    VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

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

    def _validate_id(self, id_value: str, id_type: str) -> None:
        """Validate that an ID contains only safe characters.

        Args:
            id_value: The ID to validate
            id_type: Type of ID for error messages (e.g., "scenario", "game")

        Raises:
            ValueError: If ID contains unsafe characters
        """
        if not id_value:
            raise ValueError(f"{id_type} ID cannot be empty")
        if not self.VALID_ID_PATTERN.match(id_value):
            raise ValueError(
                f"Invalid {id_type} ID '{id_value}'. "
                f"Only alphanumeric characters, hyphens, and underscores are allowed."
            )

    def get_data_dir(self) -> Path:
        return self.data_dir

    def get_saves_dir(self) -> Path:
        return self.saves_dir

    def get_scenario_dir(self, scenario_id: str) -> Path:
        self._validate_id(scenario_id, "scenario")
        scenario_dir = self.data_dir / "scenarios" / scenario_id
        return scenario_dir

    def get_save_dir(self, scenario_id: str, game_id: str, create: bool = False) -> Path:
        self._validate_id(scenario_id, "scenario")
        self._validate_id(game_id, "game")
        save_dir = self.saves_dir / scenario_id / game_id
        if create:
            save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    def get_shared_data_file(self, data_type: str) -> Path:
        return self.data_dir / f"{data_type}.json"
