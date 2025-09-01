"""Game state management service for D&D 5e game sessions."""

import uuid
from datetime import datetime

from app.common.types import JSONSerializable
from app.interfaces.services import (
    IEventManager,
    IGameService,
    IGameStateManager,
    IMessageManager,
    IMetadataService,
    ISaveManager,
    IScenarioService,
)
from app.models.character import CharacterSheet
from app.models.game_state import (
    GameEventType,
    GameState,
    GameTime,
    Message,
    MessageRole,
)
from app.models.quest import QuestStatus
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
        game_state_manager: IGameStateManager,
        message_manager: IMessageManager,
        event_manager: IEventManager,
        metadata_service: IMetadataService,
    ) -> None:
        """
        Initialize the game service.

        Args:
            scenario_service: Service for managing scenarios
            save_manager: Service for managing saves
            game_state_manager: Manager for active game states
            message_manager: Manager for conversation history
            event_manager: Manager for game events
            metadata_service: Service for extracting metadata
        """
        self.scenario_service = scenario_service
        self.save_manager = save_manager
        self.game_state_manager = game_state_manager
        self.message_manager = message_manager
        self.event_manager = event_manager
        self.metadata_service = metadata_service

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
        short_uuid = str(uuid.uuid4())[:8]
        return f"{clean_name}-{timestamp}-{short_uuid}"

    def initialize_game(
        self,
        character: CharacterSheet,
        premise: str | None = None,
        scenario_id: str | None = None,
    ) -> GameState:
        """
        Initialize a new game state.

        Args:
            character: The player's character sheet
            premise: Optional game premise or scenario
            scenario_id: Optional specific scenario to load

        Returns:
            Initialized GameState object
        """
        game_id = self.generate_game_id(character.name)

        initial_time = GameTime(
            day=1,
            hour=9,  # Start at 9 AM
            minute=0,
        )

        # Load scenario if available
        scenario = None
        if scenario_id:
            scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            scenario = self.scenario_service.get_default_scenario()

        # Set initial location and message based on scenario
        if not scenario:
            raise RuntimeError("No scenario available for game initialization. At least one scenario must be available.")

        starting_loc = scenario.get_starting_location()
        initial_location = starting_loc.name
        initial_location_id = scenario.starting_location
        initial_narrative = scenario.get_initial_narrative()
        scenario_title = scenario.title
        scenario_id = scenario.id

        initial_message = Message(
            role=MessageRole.DM,
            content=initial_narrative,
            timestamp=datetime.now(),
            agent_type="narrative",
            location=initial_location,
            npcs_mentioned=[],
            combat_round=None,
        )

        game_state = GameState(
            game_id=game_id,
            character=character,
            npcs=[],
            location=initial_location,
            current_location_id=initial_location_id,
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            current_act_id=scenario.progression.acts[0].id if scenario and scenario.progression.acts else None,
            game_time=initial_time,
            combat=None,
            quest_flags={},
            conversation_history=[initial_message],
        )

        # Initialize quests from scenario
        if scenario and scenario.quests:
            # Add the first act's quests as active
            first_act = scenario.progression.get_current_act()
            if first_act:
                for quest_id in first_act.quests:
                    quest = scenario.get_quest(quest_id)
                    if quest and quest.is_available([]):
                        quest.status = QuestStatus.ACTIVE
                        game_state.add_quest(quest)

        # Initialize starting location
        if scenario and initial_location_id:
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

    def initialize_location_from_scenario(self, game_state: GameState, scenario_location: ScenarioLocation) -> None:
        """
        Initialize a location's state from scenario data on first visit.

        This method copies static scenario data to the dynamic LocationState.
        Should only be called when a location is first encountered.

        Args:
            game_state: The game state containing location states
            scenario_location: The scenario location definition to copy from
        """
        location_state = game_state.get_location_state(scenario_location.id)
        if not location_state.visited:
            location_state.danger_level = scenario_location.danger_level
            for npc in scenario_location.npcs:
                location_state.add_npc(npc.name)

    def add_game_event(
        self,
        game_id: str,
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: dict[str, JSONSerializable] | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        """
        Add a game event to the history.

        Args:
            game_id: Game ID
            event_type: Type of event (GameEventType enum)
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool result
            metadata: Additional metadata

        Returns:
            Updated GameState
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        # Delegate to event manager
        self.event_manager.add_event(
            game_state=game_state,
            event_type=event_type,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            metadata=metadata,
        )
        self.save_game(game_state)
        return game_state

    def add_message(
        self,
        game_id: str,
        role: MessageRole,
        content: str,
        agent_type: str = "narrative",
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> GameState:
        """
        Add a message to conversation history with metadata.

        Args:
            game_id: Game ID
            role: Message role (player/dm)
            content: Message content
            agent_type: Which agent generated this message
            location: Where this message occurred
            npcs_mentioned: NPCs referenced in the message
            combat_round: Combat round if in combat

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        # Extract metadata if not provided
        if npcs_mentioned is None:
            known_npcs = [npc.name for npc in game_state.npcs]
            npcs_mentioned = self.metadata_service.extract_npcs_mentioned(content, known_npcs)

        if location is None:
            location = self.metadata_service.extract_location(content, game_state.location)

        if combat_round is None and game_state.combat:
            combat_round = self.metadata_service.extract_combat_round(content, True)

        # Delegate to message manager
        self.message_manager.add_message(
            game_state=game_state,
            role=role,
            content=content,
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned,
            combat_round=combat_round,
        )
        self.save_game(game_state)
        return game_state

    def set_quest_flag(self, game_id: str, flag_name: str, value: JSONSerializable) -> GameState:
        """
        Set a quest flag value.

        Args:
            game_id: Game ID
            flag_name: Name of the quest flag
            value: Value to set

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.quest_flags[flag_name] = value
        self.save_game(game_state)
        return game_state
