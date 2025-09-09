"""Game state management service for D&D 5e game sessions."""

from datetime import datetime

from app.agents.core.types import AgentType
from app.interfaces.services.character import ICharacterComputeService
from app.interfaces.services.data import IItemRepository
from app.interfaces.services.game import (
    IGameService,
    IGameStateManager,
    ILocationService,
    IMonsterFactory,
    ISaveManager,
)
from app.interfaces.services.scenario import IScenarioService
from app.models.character import CharacterSheet
from app.models.game_state import GameState, GameTime, Message, MessageRole
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.monster import MonsterSheet
from app.models.quest import QuestStatus
from app.models.scenario import ScenarioLocation
from app.utils.id_generator import generate_instance_id


class GameService(IGameService):
    """Service for managing game state, saves, and updates.

    Refactored to follow SOLID principles by delegating responsibilities
    to specialized managers.
    """

    def __init__(
        self,
        scenario_service: IScenarioService,
        save_manager: ISaveManager,
        game_state_manager: IGameStateManager,
        compute_service: ICharacterComputeService,
        item_repository: IItemRepository,
        monster_factory: IMonsterFactory,
        location_service: ILocationService,
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
        """
        self.scenario_service = scenario_service
        self.save_manager = save_manager
        self.game_state_manager = game_state_manager
        self.compute_service = compute_service
        self.item_repository = item_repository
        self.monster_factory = monster_factory
        self.location_service = location_service

    def generate_game_id(self, character_name: str) -> str:
        """
        Generate a human-readable game ID.

        Args:
            character_name: Name of the player character

        Returns:
            Human-readable game ID
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        clean_name = character_name.lower().replace(" ", "-")
        suffix = datetime.now().microsecond % 10000
        return f"{clean_name}-{timestamp}-{suffix:04d}"

    def initialize_game(
        self,
        character: CharacterSheet,
        scenario_id: str,
    ) -> GameState:
        """
        Initialize a new game state.

        Args:
            character: The player's character sheet
            scenario_id: Scenario to load

        Returns:
            Initialized GameState object
        """
        game_id = self.generate_game_id(character.name)

        initial_time = GameTime(
            day=1,
            hour=9,  # Start at 9 AM
            minute=0,
        )

        # Load scenario
        scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise RuntimeError(
                "No scenario available for game initialization. At least one scenario must be available."
            )

        # Set initial location and message based on scenario
        starting_loc = scenario.get_starting_location()
        initial_location = starting_loc.name
        initial_location_id = scenario.starting_location_id
        initial_narrative = scenario.get_initial_narrative()
        scenario_title = scenario.title
        scenario_id = scenario.id

        initial_message = Message(
            role=MessageRole.DM,
            content=initial_narrative,
            timestamp=datetime.now(),
            agent_type=AgentType.NARRATIVE,
            location=initial_location,
            npcs_mentioned=[],
            combat_round=None,
        )

        # Create instances
        # Materialize character instance from template starting_* fields
        char_inst = CharacterInstance(
            instance_id=generate_instance_id(character.name),
            template_id=character.id,
            sheet=character,
            state=self.compute_service.initialize_entity_state(character),
        )

        scen_inst = ScenarioInstance(
            instance_id=generate_instance_id(scenario.title),
            template_id=scenario_id,
            sheet=scenario,
            current_location_id=initial_location_id,
            current_act_id=scenario.progression.acts[0].id,
        )

        game_state = GameState(
            game_id=game_id,
            character=char_inst,
            npcs=[],
            location=initial_location,
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            scenario_instance=scen_inst,
            game_time=initial_time,
            conversation_history=[initial_message],
        )

        # Initialize quests from scenario
        if scenario.quests:
            # Add the first act's quests as active
            first_act = scenario.progression.get_current_act()
            if first_act:
                for quest_id in first_act.quests:
                    quest = scenario.get_quest(quest_id)
                    if quest and quest.is_available([]):
                        quest.status = QuestStatus.ACTIVE
                        game_state.add_quest(quest)

        # Initialize all NPCs from the scenario
        self.initialize_all_npcs(game_state)

        # Initialize starting location
        if initial_location_id:
            location = scenario.get_location(initial_location_id)
            if location:
                # Player starts here, so initialize and mark as visited
                self.initialize_location_from_scenario(game_state, location)
                game_state.get_location_state(initial_location_id).mark_visited()

        # Store in memory and save to disk
        self.game_state_manager.store_game(game_state)
        self.save_game(game_state)

        return game_state

    def save_game(self, game_state: GameState) -> str:
        """
        Save game state using modular save system.

        Args:
            game_state: Current game state to save

        Returns:
            Path to saved directory

        Raises:
            IOError: If save fails
        """
        try:
            save_dir = self.save_manager.save_game(game_state)
            return str(save_dir)
        except Exception as e:
            raise OSError(f"Failed to save game {game_state.game_id}: {e}") from e

    def load_game(self, game_id: str) -> GameState:
        """
        Load game state from modular save structure.

        Args:
            game_id: ID of the game to load

        Returns:
            Loaded GameState object

        Raises:
            FileNotFoundError: If save file doesn't exist
            ValueError: If save file is corrupted
        """
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

    def get_game(self, game_id: str) -> GameState | None:
        """
        Get active game state from memory or load from disk.

        Args:
            game_id: ID of the game

        Returns:
            GameState or None if not found
        """
        # Check in-memory storage first
        game_state = self.game_state_manager.get_game(game_id)
        if game_state:
            return game_state

        # Try loading from disk
        try:
            return self.load_game(game_id)
        except (FileNotFoundError, ValueError):
            return None

    def list_saved_games(self) -> list[GameState]:
        """
        List all saved games.

        Returns:
            List of GameState objects for all saved games
        """
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
        """
        Remove a game from memory.

        Args:
            game_id: ID of the game to remove
        """
        self.game_state_manager.remove_game(game_id)

    def create_monster_instance(self, sheet: MonsterSheet, current_location_id: str) -> MonsterInstance:
        """Create a MonsterInstance from a MonsterSheet (delegates to factory)."""
        return self.monster_factory.create(sheet, current_location_id)

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        """Delegate to LocationService for first-visit initialization."""
        self.location_service.initialize_location_from_scenario(game_state, scenario_location)

    def recompute_character_state(self, game_state: GameState) -> None:
        """Recompute derived values for the player character using the compute service."""
        char = game_state.character
        new_state = self.compute_service.recompute_entity_state(char.sheet, char.state)
        char.state = new_state
        char.touch()

    def initialize_all_npcs(self, game_state: GameState) -> None:
        """
        Initialize all NPCInstances from the scenario at game start.

        Creates NPCInstance objects for all NPCs defined in the scenario,
        setting their initial locations.

        Args:
            game_state: The game state to update
        """
        if not game_state.scenario_id:
            return

        # Load all NPCs from the scenario directory
        npc_sheets = self.scenario_service.list_scenario_npcs(game_state.scenario_id)

        # Create an instance for each NPC in the scenario
        # NOTE: For MVP1, all NPCs are loaded at game start regardless of location.
        # TODO(MVP2): Future enhancement could implement lazy loading based on location proximity.
        for npc_sheet in npc_sheets:
            # Create NPCInstance with initial location
            npc_instance = NPCInstance(
                instance_id=generate_instance_id(npc_sheet.display_name),
                scenario_npc_id=npc_sheet.id,
                sheet=npc_sheet,
                state=self.compute_service.initialize_entity_state(npc_sheet.character),
                current_location_id=npc_sheet.initial_location_id,
                attitude=npc_sheet.initial_attitude,
                notes=list(npc_sheet.initial_notes) if npc_sheet.initial_notes else [],
            )

            game_state.npcs.append(npc_instance)
