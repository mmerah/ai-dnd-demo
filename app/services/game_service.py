"""Game state management service for D&D 5e game sessions."""

import json
import uuid
from datetime import datetime

from app.config import get_settings
from app.interfaces.services import IGameService
from app.models.character import CharacterSheet, Item
from app.models.game_state import (
    CombatParticipant,
    CombatState,
    GameState,
    GameTime,
    JSONSerializable,
    Message,
    MessageRole,
)
from app.models.npc import NPCSheet
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
            initial_location = "The Prancing Pony Tavern"
            initial_location_id = None
            initial_narrative = premise or "Your adventure begins in the bustling tavern 'The Prancing Pony'..."
            scenario_title = None
            scenario_id = None

        initial_message = Message(role=MessageRole.DM, content=initial_narrative, timestamp=datetime.now())

        game_state = GameState(
            game_id=game_id,
            character=character,
            npcs=[],
            location=initial_location,
            current_location_id=initial_location_id,
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            game_time=initial_time,
            combat=None,
            quest_flags={},
            conversation_history=[initial_message],
        )

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

    def update_character_hp(self, game_id: str, amount: int, target: str = "player") -> GameState:
        """
        Update HP for character or NPC.

        Args:
            game_id: Game ID
            amount: HP change (negative for damage, positive for healing)
            target: "player" or NPC name

        Returns:
            Updated GameState

        Raises:
            ValueError: If game or target not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        if target == "player":
            new_hp = game_state.character.hit_points.current + amount
            game_state.character.hit_points.current = max(0, min(new_hp, game_state.character.hit_points.maximum))
        else:
            npc = next((n for n in game_state.npcs if n.name == target), None)
            if not npc:
                raise ValueError(f"NPC {target} not found")
            new_hp = npc.hit_points.current + amount
            npc.hit_points.current = max(0, min(new_hp, npc.hit_points.maximum))

        self.save_game(game_state)
        return game_state

    def add_npc(self, game_id: str, npc: NPCSheet) -> GameState:
        """
        Add an NPC to the game.

        Args:
            game_id: Game ID
            npc: NPC to add

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.npcs.append(npc)
        self.save_game(game_state)
        return game_state

    def remove_npc(self, game_id: str, npc_name: str) -> GameState:
        """
        Remove an NPC from the game.

        Args:
            game_id: Game ID
            npc_name: Name of NPC to remove

        Returns:
            Updated GameState

        Raises:
            ValueError: If game or NPC not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.npcs = [n for n in game_state.npcs if n.name != npc_name]
        self.save_game(game_state)
        return game_state

    def start_combat(self, game_id: str, participants: list[CombatParticipant]) -> GameState:
        """
        Initialize combat state.

        Args:
            game_id: Game ID
            participants: List of combat participants with initiative

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        combat_state = CombatState(round_number=1, turn_index=0, participants=participants)

        game_state.combat = combat_state
        self.save_game(game_state)
        return game_state

    def end_combat(self, game_id: str) -> GameState:
        """
        End combat and clear combat state.

        Args:
            game_id: Game ID

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.combat = None
        self.save_game(game_state)
        return game_state

    def advance_time(self, game_id: str, minutes: int) -> GameState:
        """
        Advance game time.

        Args:
            game_id: Game ID
            minutes: Minutes to advance

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        total_minutes = game_state.game_time.minute + minutes
        hours_to_add = total_minutes // 60
        game_state.game_time.minute = total_minutes % 60

        total_hours = game_state.game_time.hour + hours_to_add
        days_to_add = total_hours // 24
        game_state.game_time.hour = total_hours % 24

        game_state.game_time.day += days_to_add

        self.save_game(game_state)
        return game_state

    def update_location(self, game_id: str, location: str) -> GameState:
        """
        Update the current location.

        Args:
            game_id: Game ID
            location: New location name

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        game_state.location = location
        self.save_game(game_state)
        return game_state

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

    def add_message(self, game_id: str, role: MessageRole, content: str) -> GameState:
        """
        Add a message to conversation history.

        Args:
            game_id: Game ID
            role: Message role (user/assistant/system)
            content: Message content

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        message = Message(role=role, content=content, timestamp=datetime.now())

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

    def modify_currency(self, game_id: str, gold: int = 0, silver: int = 0, copper: int = 0) -> GameState:
        """
        Modify character's currency.

        Args:
            game_id: Game ID
            gold: Gold to add/subtract
            silver: Silver to add/subtract
            copper: Copper to add/subtract

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found or insufficient funds
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        currency = game_state.character.currency

        currency.gold = max(0, currency.gold + gold)
        currency.silver = max(0, currency.silver + silver)
        currency.copper = max(0, currency.copper + copper)

        self.save_game(game_state)
        return game_state

    def add_item(self, game_id: str, item_name: str, quantity: int = 1) -> GameState:
        """
        Add item to character's inventory.

        Args:
            game_id: Game ID
            item_name: Name of item to add
            quantity: Quantity to add

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        inventory = game_state.character.inventory

        existing_item = next((item for item in inventory if item.name == item_name), None)

        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = Item(name=item_name, quantity=quantity, weight=0.0, value=0.0)
            inventory.append(new_item)

        self.save_game(game_state)
        return game_state

    def remove_item(self, game_id: str, item_name: str, quantity: int = 1) -> GameState:
        """
        Remove item from character's inventory.

        Args:
            game_id: Game ID
            item_name: Name of item to remove
            quantity: Quantity to remove

        Returns:
            Updated GameState

        Raises:
            ValueError: If game not found or item not in inventory
        """
        game_state = self.get_game(game_id)
        if not game_state:
            raise ValueError(f"Game {game_id} not found")

        inventory = game_state.character.inventory

        item = next((item for item in inventory if item.name == item_name), None)

        if not item:
            raise ValueError(f"Item {item_name} not found in inventory")

        if item.quantity < quantity:
            raise ValueError(f"Not enough {item_name} in inventory")

        item.quantity -= quantity

        if item.quantity == 0:
            inventory.remove(item)

        self.save_game(game_state)
        return game_state
