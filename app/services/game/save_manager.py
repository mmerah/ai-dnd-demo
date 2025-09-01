"""Save manager for modular game state persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.interfaces.services import IPathResolver, ISaveManager
from app.models.character import CharacterSheet
from app.models.combat import CombatState
from app.models.game_state import GameEvent, GameState, GameTime, Message
from app.models.location import LocationState
from app.models.npc import NPCSheet
from app.models.quest import Quest

logger = logging.getLogger(__name__)


class SaveManager(ISaveManager):
    """Manages save/load operations with modular file structure.

    Follows Single Responsibility Principle: only handles save orchestration.
    Delegates component-specific operations to dedicated methods.
    """

    def __init__(self, path_resolver: IPathResolver):
        """Initialize save manager.

        Args:
            path_resolver: Service for resolving file paths
        """
        self.path_resolver = path_resolver

    def save_game(self, game_state: GameState) -> Path:
        """Save complete game state to modular structure.

        Creates the following structure:
        saves/[scenario-id]/[game-id]/
            ├── metadata.json
            ├── character.json
            ├── conversation_history.json
            ├── game_events.json
            ├── location_states/
            │   └── [location-id].json
            ├── npcs/
            │   └── [npc-name].json
            └── quests/
                └── [quest-id].json

        Args:
            game_state: Game state to save

        Returns:
            Path to the save directory
        """
        # Get save directory
        scenario_id = game_state.scenario_id or "unknown"
        save_dir = self.path_resolver.get_save_dir(scenario_id, game_state.game_id, create=True)

        # Update save timestamp
        game_state.update_save_time()

        # Save each component
        self._save_metadata(save_dir, game_state)
        self._save_character(save_dir, game_state.character)
        self._save_conversation_history(save_dir, game_state.conversation_history)
        self._save_game_events(save_dir, game_state.game_events)
        self._save_location_states(save_dir, game_state.location_states)
        self._save_npcs(save_dir, game_state.npcs)
        self._save_quests(save_dir, game_state.active_quests)

        # Save combat state if active
        if game_state.combat:
            self._save_combat(save_dir, game_state.combat)

        return save_dir

    def load_game(self, scenario_id: str, game_id: str) -> GameState:
        """Load complete game state from modular structure.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            Loaded game state

        Raises:
            FileNotFoundError: If save doesn't exist
            RuntimeError: If loading fails
        """
        save_dir = self.path_resolver.get_save_dir(scenario_id, game_id, create=False)

        if not (save_dir / "metadata.json").exists():
            raise FileNotFoundError(f"No save found for {scenario_id}/{game_id}")

        try:
            # Load metadata first
            metadata = self._load_metadata(save_dir)

            # Load character first as it's required for GameState
            character = self._load_character(save_dir)

            # Create base game state from metadata with proper type casting
            game_state = GameState(
                game_id=str(metadata["game_id"]),
                created_at=datetime.fromisoformat(str(metadata["created_at"])),
                last_saved=datetime.fromisoformat(str(metadata["last_saved"])),
                scenario_id=str(metadata["scenario_id"]) if metadata.get("scenario_id") else None,
                scenario_title=str(metadata["scenario_title"]) if metadata.get("scenario_title") else None,
                current_location_id=str(metadata["current_location_id"])
                if metadata.get("current_location_id")
                else None,
                current_act_id=str(metadata["current_act_id"]) if metadata.get("current_act_id") else None,
                location=str(metadata.get("location", "Unknown")),
                description=str(metadata.get("description", "")),
                game_time=GameTime(**dict(metadata.get("game_time", {}))),
                quest_flags=dict(metadata.get("quest_flags", {})),
                story_notes=list(metadata.get("story_notes", [])),
                completed_quest_ids=list(metadata.get("completed_quest_ids", [])),
                active_agent=str(metadata.get("active_agent", "narrative")),
                session_number=int(metadata.get("session_number", 1)),
                total_play_time_minutes=int(metadata.get("total_play_time_minutes", 0)),
                # Core required field
                character=character,
                # These will be loaded separately
                conversation_history=[],
                game_events=[],
                location_states={},
                npcs=[],
                active_quests=[],
                combat=None,
            )

            # Load remaining components
            game_state.conversation_history = self._load_conversation_history(save_dir)
            game_state.game_events = self._load_game_events(save_dir)
            game_state.location_states = self._load_location_states(save_dir)
            game_state.npcs = self._load_npcs(save_dir)
            game_state.active_quests = self._load_quests(save_dir)

            # Load combat if exists
            if (save_dir / "combat.json").exists():
                game_state.combat = self._load_combat(save_dir)

            return game_state

        except Exception as e:
            raise RuntimeError(f"Failed to load game {scenario_id}/{game_id}: {e}") from e

    def list_saved_games(self, scenario_id: str | None = None) -> list[tuple[str, str, datetime]]:
        """List all saved games.

        Args:
            scenario_id: Optional filter by scenario

        Returns:
            List of (scenario_id, game_id, last_saved) tuples
        """
        saves_dir = self.path_resolver.get_saves_dir()
        games = []

        # If scenario_id provided, only check that scenario
        if scenario_id:
            scenario_dir = saves_dir / scenario_id
            if scenario_dir.exists():
                for game_dir in scenario_dir.iterdir():
                    if game_dir.is_dir():
                        metadata_file = game_dir / "metadata.json"
                        if metadata_file.exists():
                            try:
                                with open(metadata_file, encoding="utf-8") as f:
                                    metadata = json.load(f)
                                last_saved = datetime.fromisoformat(metadata["last_saved"])
                                games.append((scenario_id, game_dir.name, last_saved))
                            except (json.JSONDecodeError, KeyError, ValueError) as e:
                                logger.warning(
                                    f"Failed to parse metadata for {game_dir.name}: {e.__class__.__name__}: {e}"
                                )
                                continue
        else:
            # Check all scenarios
            for scenario_dir in saves_dir.iterdir():
                if scenario_dir.is_dir():
                    for game_dir in scenario_dir.iterdir():
                        if game_dir.is_dir():
                            metadata_file = game_dir / "metadata.json"
                            if metadata_file.exists():
                                try:
                                    with open(metadata_file, encoding="utf-8") as f:
                                        metadata = json.load(f)
                                    last_saved = datetime.fromisoformat(metadata["last_saved"])
                                    games.append((scenario_dir.name, game_dir.name, last_saved))
                                except (json.JSONDecodeError, KeyError, ValueError) as e:
                                    logger.warning(
                                        f"Failed to parse metadata for {game_dir.name}: {e.__class__.__name__}: {e}"
                                    )
                                    continue

        # Sort by last_saved descending
        games.sort(key=lambda x: x[2], reverse=True)
        return games

    def game_exists(self, scenario_id: str, game_id: str) -> bool:
        """Check if a saved game exists.

        Args:
            scenario_id: ID of the scenario
            game_id: ID of the game

        Returns:
            True if save exists
        """
        save_dir = self.path_resolver.get_save_dir(scenario_id, game_id, create=False)
        return (save_dir / "metadata.json").exists()

    # Component save methods

    def _save_metadata(self, save_dir: Path, game_state: GameState) -> None:
        """Save game metadata."""
        metadata = {
            "game_id": game_state.game_id,
            "created_at": game_state.created_at.isoformat(),
            "last_saved": game_state.last_saved.isoformat(),
            "scenario_id": game_state.scenario_id,
            "scenario_title": game_state.scenario_title,
            "current_location_id": game_state.current_location_id,
            "current_act_id": game_state.current_act_id,
            "location": game_state.location,
            "description": game_state.description,
            "game_time": game_state.game_time.model_dump(),
            "quest_flags": game_state.quest_flags,
            "story_notes": game_state.story_notes,
            "completed_quest_ids": game_state.completed_quest_ids,
            "active_agent": game_state.active_agent,
            "session_number": game_state.session_number,
            "total_play_time_minutes": game_state.total_play_time_minutes,
        }

        with open(save_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def _save_character(self, save_dir: Path, character: CharacterSheet) -> None:
        """Save character state."""
        with open(save_dir / "character.json", "w", encoding="utf-8") as f:
            f.write(character.model_dump_json(indent=2))

    def _save_conversation_history(self, save_dir: Path, messages: list[Message]) -> None:
        """Save conversation history."""
        history_data = [msg.model_dump(mode="json") for msg in messages]
        with open(save_dir / "conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)

    def _save_game_events(self, save_dir: Path, events: list[GameEvent]) -> None:
        """Save game events."""
        events_data = [event.model_dump(mode="json") for event in events]
        with open(save_dir / "game_events.json", "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=2)

    def _save_location_states(self, save_dir: Path, location_states: dict[str, LocationState]) -> None:
        """Save location states."""
        location_dir = save_dir / "location_states"
        location_dir.mkdir(exist_ok=True)

        for location_id, state in location_states.items():
            file_path = location_dir / f"{location_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))

    def _save_npcs(self, save_dir: Path, npcs: list[NPCSheet]) -> None:
        """Save NPCs."""
        npcs_dir = save_dir / "npcs"
        npcs_dir.mkdir(exist_ok=True)

        for i, npc in enumerate(npcs):
            # Use index-name combination to handle duplicates
            safe_name = npc.name.replace(" ", "-").replace("/", "-").lower()
            file_path = npcs_dir / f"{i:03d}-{safe_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(npc.model_dump_json(indent=2))

    def _save_quests(self, save_dir: Path, quests: list[Quest]) -> None:
        """Save active quests."""
        quests_dir = save_dir / "quests"
        quests_dir.mkdir(exist_ok=True)

        for quest in quests:
            file_path = quests_dir / f"{quest.id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(quest.model_dump_json(indent=2))

    def _save_combat(self, save_dir: Path, combat: CombatState) -> None:
        """Save combat state."""
        with open(save_dir / "combat.json", "w", encoding="utf-8") as f:
            f.write(combat.model_dump_json(indent=2))

    # Component load methods

    def _load_metadata(self, save_dir: Path) -> dict[str, Any]:
        """Load game metadata.

        Returns dict from JSON - proper typing is handled by the caller.
        """
        with open(save_dir / "metadata.json", encoding="utf-8") as f:
            # json.load returns Any, which is what we need for metadata
            data: dict[str, Any] = json.load(f)
            return data

    def _load_character(self, save_dir: Path) -> CharacterSheet:
        """Load character state."""
        with open(save_dir / "character.json", encoding="utf-8") as f:
            data = json.load(f)
        return CharacterSheet(**data)

    def _load_conversation_history(self, save_dir: Path) -> list[Message]:
        """Load conversation history."""
        file_path = save_dir / "conversation_history.json"
        if not file_path.exists():
            return []

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return [Message(**msg_data) for msg_data in data]

    def _load_game_events(self, save_dir: Path) -> list[GameEvent]:
        """Load game events."""
        file_path = save_dir / "game_events.json"
        if not file_path.exists():
            return []

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return [GameEvent(**event_data) for event_data in data]

    def _load_location_states(self, save_dir: Path) -> dict[str, LocationState]:
        """Load location states."""
        location_dir = save_dir / "location_states"
        if not location_dir.exists():
            return {}

        states = {}
        for file_path in location_dir.glob("*.json"):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            state = LocationState(**data)
            states[state.location_id] = state

        return states

    def _load_npcs(self, save_dir: Path) -> list[NPCSheet]:
        """Load NPCs."""
        npcs_dir = save_dir / "npcs"
        if not npcs_dir.exists():
            return []

        npcs = []
        # Load in sorted order to preserve original ordering
        for file_path in sorted(npcs_dir.glob("*.json")):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            npcs.append(NPCSheet(**data))

        return npcs

    def _load_quests(self, save_dir: Path) -> list[Quest]:
        """Load active quests."""
        quests_dir = save_dir / "quests"
        if not quests_dir.exists():
            return []

        quests = []
        for file_path in quests_dir.glob("*.json"):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            quests.append(Quest(**data))

        return quests

    def _load_combat(self, save_dir: Path) -> CombatState | None:
        """Load combat state."""
        file_path = save_dir / "combat.json"
        if not file_path.exists():
            return None

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return CombatState(**data)
