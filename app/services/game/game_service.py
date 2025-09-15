"""Game state management service for D&D 5e game sessions."""

from app.interfaces.services.game import (
    IGameFactory,
    IGameService,
    IGameStateManager,
    IPreSaveSanitizer,
    ISaveManager,
)
from app.models.character import CharacterSheet
from app.models.game_state import GameState


class GameService(IGameService):
    """Service for managing game state, saves, and updates.

    Refactored to follow SOLID principles by delegating responsibilities
    to specialized managers.
    """

    def __init__(
        self,
        save_manager: ISaveManager,
        pre_save_sanitizer: IPreSaveSanitizer,
        game_state_manager: IGameStateManager,
        game_factory: IGameFactory,
    ) -> None:
        """
        Initialize the game service.

        Args:
            save_manager: Service for managing saves
            pre_save_sanitizer: Service to sanitize saves before saving to disk
            game_state_manager: Manager for active game states
            location_service: Service for managing location state
            game_factory: Factory for creating new game instances
        """
        self.save_manager = save_manager
        self.pre_save_sanitizer = pre_save_sanitizer
        self.game_state_manager = game_state_manager
        self.game_factory = game_factory

    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
        content_packs: list[str] | None = None,
    ) -> GameState:
        # Delegate initialization to the factory
        game_state = self.game_factory.initialize_game(character, scenario_id, content_packs)

        # Store in memory and save to disk
        self.game_state_manager.store_game(game_state)
        self.save_game(game_state)

        return game_state

    def save_game(self, game_state: GameState) -> str:
        try:
            # Pre-save sanitization step to avoid SaveManager mutating state inline
            self.pre_save_sanitizer.sanitize(game_state)
            save_dir = self.save_manager.save_game(game_state)
            return str(save_dir)
        except Exception as e:
            raise OSError(f"Failed to save game {game_state.game_id}: {e}") from e

    def load_game(self, game_id: str) -> GameState:
        # First, try to find the game by searching through saved games
        saved_games = self.save_manager.list_saved_games()

        scenario_id = None
        for saved_scenario_id, saved_game_id, _ in saved_games:
            if saved_game_id == game_id:
                scenario_id = saved_scenario_id
                break

        if scenario_id is None:
            raise FileNotFoundError(f"No save file found for game {game_id}")

        try:
            game_state = self.save_manager.load_game(scenario_id, game_id)
            # Store in memory after loading
            self.game_state_manager.store_game(game_state)
            return game_state
        except Exception as e:
            raise ValueError(f"Failed to load game {game_id}: {e}") from e

    def get_game(self, game_id: str) -> GameState:
        # Check in-memory storage first
        game_state = self.game_state_manager.get_game(game_id)
        if game_state:
            return game_state

        # Try loading from disk
        return self.load_game(game_id)

    def list_saved_games(self) -> list[GameState]:
        games = []
        saved_games = self.save_manager.list_saved_games()

        for scenario_id, game_id, _ in saved_games:
            try:
                game_state = self.save_manager.load_game(scenario_id, game_id)
                games.append(game_state)
            except Exception:
                # Skip corrupted save files
                continue

        # Already sorted by last_saved from save_manager
        return games

    def remove_game(self, game_id: str) -> None:
        self.game_state_manager.remove_game(game_id)
