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
        """Publish an SSE event with Pydantic model data.

        Args:
            game_id: ID of the game to publish to
            event: Event type/name
            data: Pydantic model data to broadcast
        """
        pass

    @abstractmethod
    def subscribe(self, game_id: str) -> AsyncGenerator[dict[str, str], None]:
        """Subscribe to SSE events for a game.

        Args:
            game_id: ID of the game to subscribe to

        Yields:
            Formatted SSE dictionaries with 'event' and 'data' keys
        """
        pass


class IPathResolver(ABC):
    """Interface for resolving file paths in the application."""

    @abstractmethod
    def get_data_dir(self) -> Path:
        """Get the root data directory.

        Returns:
            Path to the data directory containing game data files
        """
        pass

    @abstractmethod
    def get_saves_dir(self) -> Path:
        """Get the root saves directory.

        Returns:
            Path to the directory where game saves are stored
        """
        pass

    @abstractmethod
    def get_scenario_dir(self, scenario_id: str) -> Path:
        """Get directory for a specific scenario.

        Args:
            scenario_id: ID of the scenario

        Returns:
            Path to the scenario's data directory
        """
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
        """Get path to a shared data file.

        Args:
            data_type: Type of data ('items', 'spells', 'monsters', etc.)

        Returns:
            Path to the shared data file
        """
        pass


class IDiceService(ABC):
    """Interface for dice rolling mechanics."""

    @abstractmethod
    def parse_dice_formula(self, formula: str) -> tuple[int, int, int]:
        """Parse a dice formula into components.

        Examples:
        - '2d6+3' -> (2, 6, 3)
        - 'd20-5' -> (1, 20, -5)
        - '3d8' -> (3, 8, 0)

        Args:
            formula: Dice formula string

        Returns:
            Tuple of (count, sides, modifier)

        Raises:
            ValueError: If formula is invalid
        """
        pass

    @abstractmethod
    def roll_dice(self, formula: str, roll_type: RollType = RollType.NORMAL) -> DiceRoll:
        """Roll dice based on formula with optional advantage/disadvantage.

        Args:
            formula: Dice formula (e.g., '2d6+3', 'd20')
            roll_type: NORMAL, ADVANTAGE, or DISADVANTAGE

        Returns:
            DiceRoll result with individual rolls and total
        """
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
        """Execute a command as an action with unified tracking and broadcasting.

        This method wraps command execution with:
        - Event logging and persistence
        - SSE broadcasting of tool calls and results
        - Automatic game state saving after execution

        Args:
            tool_name: Name of the tool executing the command
            command: Command to execute
            game_state: Current game state
            broadcast_parameters: Optional parameters to include in broadcast

        Returns:
            Result model from command execution
        """
        pass
