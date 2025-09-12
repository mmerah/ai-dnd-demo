"""Game state management service for D&D 5e game sessions."""

from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.data import IItemRepository
from app.interfaces.services.game import (
    IGameFactory,
    IGameService,
    IGameStateManager,
    ILocationService,
    IMonsterFactory,
    IPreSaveSanitizer,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.models.instances.monster_instance import MonsterInstance
from app.models.monster import MonsterSheet
from app.models.scenario import ScenarioLocation


class GameService(IGameService):
    """Service for managing game state, saves, and updates.

    Refactored to follow SOLID principles by delegating responsibilities
    to specialized managers.
    """

    def __init__(
        self,
        scenario_service: IScenarioService,
        save_manager: ISaveManager,
        pre_save_sanitizer: IPreSaveSanitizer,
        game_state_manager: IGameStateManager,
        compute_service: ICharacterComputeService,
        item_repository: IItemRepository,
        monster_factory: IMonsterFactory,
        location_service: ILocationService,
        game_factory: IGameFactory,
    ) -> None:
        """
        Initialize the game service.

        Args:
            scenario_service: Service for managing scenarios
            save_manager: Service for managing saves
            game_state_manager: Manager for active game states
            compute_service: Service for computing derived character values
            item_repository: Repository for all items of the game
            monster_factory: Factory to MonsterInstance from a MonsterSheet
            location_service: Service for managing location state
            game_factory: Factory for creating new game instances
        """
        self.scenario_service = scenario_service
        self.save_manager = save_manager
        self.pre_save_sanitizer = pre_save_sanitizer
        self.game_state_manager = game_state_manager
        self.compute_service = compute_service
        self.item_repository = item_repository
        self.monster_factory = monster_factory
        self.location_service = location_service
        self.game_factory = game_factory

    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
    ) -> GameState:
        # Delegate initialization to the factory
        game_state = self.game_factory.initialize_game(character, scenario_id)

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

    def create_monster_instance(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        return self.monster_factory.create(sheet, current_location_id)

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        self.location_service.initialize_location_from_scenario(game_state, scenario_location)

    def recompute_character_state(self, game_state: GameState) -> None:
        char = game_state.character
        new_state = self.compute_service.recompute_entity_state(char.sheet, char.state)
        char.state = new_state
        char.touch()
