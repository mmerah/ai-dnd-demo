"""Game state management service for D&D 5e game sessions."""

import json
import uuid
from datetime import datetime

from app.config import get_settings
from app.interfaces.services import IGameService
from app.models.character import CharacterSheet
from app.models.game_state import (
    GameState,
    GameTime,
    JSONSerializable,
    Message,
    MessageRole,
)
from app.models.quest import QuestStatus
from app.services.scenario_service import ScenarioService


class GameService(IGameService):
    """Service for managing game state, saves, and updates."""

    def __init__(self) -> None:
        """
        Initialize the game service with configuration from settings.
        """
        settings = get_settings()
        self.save_directory = settings.save_directory
        # Directory already created in Settings __init__
        self._active_games: dict[str, GameState] = {}
        self.scenario_service = ScenarioService()

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
        self, character: CharacterSheet, premise: str | None = None, scenario_id: str | None = None
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
        if scenario:
            starting_loc = scenario.get_starting_location()
            initial_location = starting_loc.name if starting_loc else "The Wandering Griffin Tavern"
            initial_location_id = scenario.starting_location
            initial_narrative = scenario.get_initial_narrative()
            scenario_title = scenario.title
            scenario_id = scenario.id
        else:
            # TODO: Raise error, there should be a scenario ?
            initial_location = "The Prancing Pony Tavern"
            initial_location_id = None
            initial_narrative = premise or "Your adventure begins in the bustling tavern 'The Prancing Pony'..."
            scenario_title = None
            scenario_id = None

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

        self._active_games[game_id] = game_state
        self.save_game(game_state)

        return game_state

    def save_game(self, game_state: GameState) -> str:
        """
        Save game state to JSON file.

        Args:
            game_state: Current game state to save

        Returns:
            Path to saved file

        Raises:
            IOError: If save fails
        """
        save_path = self.save_directory / f"{game_state.game_id}.json"

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                # Use model_dump_json for proper datetime serialization
                json_data = game_state.model_dump_json(indent=2)
                f.write(json_data)
            return str(save_path)
        except Exception as e:
            raise OSError(f"Failed to save game {game_state.game_id}: {e}") from e

    def load_game(self, game_id: str) -> GameState:
        """
        Load game state from JSON file.

        Args:
            game_id: ID of the game to load

        Returns:
            Loaded GameState object

        Raises:
            FileNotFoundError: If save file doesn't exist
            ValueError: If save file is corrupted
        """
        save_path = self.save_directory / f"{game_id}.json"

        if not save_path.exists():
            raise FileNotFoundError(f"No save file found for game {game_id}")

        try:
            with open(save_path, encoding="utf-8") as f:
                data = json.load(f)

            game_state = GameState.model_validate(data)
            self._active_games[game_id] = game_state
            return game_state

        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted save file for game {game_id}: {e}") from e
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
        if game_id in self._active_games:
            return self._active_games[game_id]

        try:
            return self.load_game(game_id)
        except (FileNotFoundError, ValueError):
            return None

    def list_saved_games(self) -> list[dict[str, str]]:
        """
        List all saved games.

        Returns:
            List of game summaries with id, character name, and last modified
        """
        games = []

        for save_file in self.save_directory.glob("*.json"):
            try:
                with open(save_file, encoding="utf-8") as f:
                    data = json.load(f)

                games.append(
                    {
                        "game_id": data["game_id"],
                        "character_name": data["character"]["name"],
                        "location": data["location"],
                        "last_modified": datetime.fromtimestamp(save_file.stat().st_mtime).isoformat(),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

        return sorted(games, key=lambda x: x["last_modified"], reverse=True)

    def add_game_event(
        self,
        game_id: str,
        event_type: str,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: JSONSerializable | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> GameState:
        """
        Add a game event to the history.

        Args:
            game_id: Game ID
            event_type: Type of event (tool_call, tool_result, etc.)
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

        # Import here to avoid circular dependency
        from app.models.game_state import GameEventType

        game_state.add_game_event(
            event_type=GameEventType(event_type),
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

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned if npcs_mentioned is not None else [],
            combat_round=combat_round,
        )

        game_state.conversation_history.append(message)
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
