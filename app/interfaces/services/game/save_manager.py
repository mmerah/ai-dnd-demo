"""Interface for save manager."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.models.game_state import GameState


class ISaveManager(ABC):
    """Interface for managing game save operations."""

    @abstractmethod
    def save_game(self, game_state: GameState) -> Path:
        """Save complete game state to modular structure.

        Creates the following structure:
        saves/[scenario-id]/[game-id]/
            ├── metadata.json
            ├── instances/
            │   ├── character.json
            │   ├── scenario.json
            │   ├── npcs/
            │   │    └── [npc-instance-id].json
            |   └── monsters/
            │       └── [monster-instance-id].json
            ├── conversation_history.json
            └── game_events.json

        Args:
            game_state: Game state to save

        Returns:
            Path to the save directory
        """
        pass

    @abstractmethod
    def load_game(self, scenario_id: str, game_id: str) -> GameState:
        """Load complete game state from modular structure.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            Loaded game state
        """
        pass

    @abstractmethod
    def list_saved_games(self, scenario_id: str | None = None) -> list[tuple[str, str, datetime]]:
        """List all saved games.

        Args:
            scenario_id: Optional filter by scenario

        Returns:
            List of (scenario_id, game_id, last_saved) tuples
        """
        pass
