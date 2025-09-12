from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.models.dice import DiceRoll, RollType
from app.models.game_state import GameState

T = TypeVar("T")


class IBroadcastService(ABC):
    """Interface for the pub/sub SSE event streaming service.

    The data parameter expects Pydantic BaseModel instances that can be
    serialized to JSON for SSE transmission.
    """

    @abstractmethod
    async def publish(self, game_id: str, event: str, data: BaseModel) -> None:
        """Publish an SSE event with Pydantic model data."""
        pass

    @abstractmethod
    def subscribe(self, game_id: str) -> AsyncGenerator[dict[str, str], None]:
        """Subscribe to SSE events, yields formatted SSE dictionaries."""
        pass


class IPathResolver(ABC):
    """Interface for resolving file paths in the application."""

    @abstractmethod
    def get_data_dir(self) -> Path:
        """Get the root data directory."""
        pass

    @abstractmethod
    def get_saves_dir(self) -> Path:
        """Get the root saves directory."""
        pass

    @abstractmethod
    def get_scenario_dir(self, scenario_id: str) -> Path:
        """Get directory for a specific scenario."""
        pass

    @abstractmethod
    def get_save_dir(self, scenario_id: str, game_id: str, create: bool = False) -> Path:
        """Get directory for a saved game.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game
            create: If True, create the directory if it doesn't exist
        """
        pass

    @abstractmethod
    def get_shared_data_file(self, data_type: str) -> Path:
        """Get path to a shared data file (items, spells, monsters)."""
        pass


class IDiceService(ABC):
    """Interface for dice rolling mechanics."""

    @abstractmethod
    def parse_dice_formula(self, formula: str) -> tuple[int, int, int]:
        """Parse a dice formula like '2d6+3' into (count, sides, mod)."""
        pass

    @abstractmethod
    def roll_dice(self, formula: str, roll_type: RollType = RollType.NORMAL) -> DiceRoll:
        """Roll dice based on formula with optional advantage/disadvantage."""
        pass


class IActionService(ABC):
    """Execute commands as actions with unified tracking and broadcasting."""

    @abstractmethod
    async def execute_command_as_action(
        self,
        tool_name: str,
        command: BaseCommand,
        game_state: GameState,
        broadcast_parameters: dict[str, JSONSerializable] | None = None,
    ) -> BaseModel:
        """Execute a command as an action, broadcasting and persisting events."""
        pass
