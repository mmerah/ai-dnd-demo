"""Save manager for modular game state persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.interfaces.services.common import IPathResolver
from app.interfaces.services.game import ISaveManager
from app.models.combat import CombatState
from app.models.game_state import GameEvent, GameState, Message
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.instances.scenario_instance import ScenarioInstance

logger = logging.getLogger(__name__)


class SaveManager(ISaveManager):
    """Manages save/load operations with modular file structure."""

    def __init__(self, path_resolver: IPathResolver):
        """Initialize save manager.

        Args:
            path_resolver: Service for resolving file paths
        """
        self.path_resolver = path_resolver

    def save_game(self, game_state: GameState) -> Path:
        # Get save directory
        scenario_id = game_state.scenario_id
        save_dir = self.path_resolver.get_save_dir(scenario_id, game_state.game_id, create=True)

        # Update save timestamp
        game_state.update_save_time()

        # Save each component
        self._save_metadata(save_dir, game_state)
        self._save_instances(save_dir, game_state)
        self._save_conversation_history(save_dir, game_state.conversation_history)
        self._save_game_events(save_dir, game_state.game_events)

        # Save only alive monsters (redundant but ensures consistency)
        alive_monsters = [m for m in game_state.monsters if m.is_alive()]
        self._save_monster_instances(save_dir, alive_monsters)

        # Save combat state if active, delete if inactive
        combat_file = save_dir / "combat.json"
        if game_state.combat.is_active:
            self._save_combat(save_dir, game_state.combat)
        elif combat_file.exists():
            # Clean up stale combat file when combat is no longer active
            combat_file.unlink()
            logger.debug(f"Removed inactive combat.json for game {game_state.game_id}")

        return save_dir

    def load_game(self, scenario_id: str, game_id: str) -> GameState:
        save_dir = self.path_resolver.get_save_dir(scenario_id, game_id, create=False)

        if not (save_dir / "metadata.json").exists():
            raise FileNotFoundError(f"No save found for {scenario_id}/{game_id}")

        try:
            # Load metadata first
            try:
                metadata = self._load_metadata(save_dir)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Cannot load game {game_id}: {e}") from e
            except ValueError as e:
                raise ValueError(f"Cannot load game {game_id}: {e}") from e

            # Load instances and other components
            try:
                character = self._load_character_instance(save_dir)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Cannot load game {game_id}: {e}") from e
            except ValueError as e:
                raise ValueError(f"Cannot load game {game_id}: {e}") from e
            try:
                scenario_instance = self._load_scenario_instance(save_dir)
            except FileNotFoundError as e:
                # Re-raise with game context
                raise FileNotFoundError(f"Cannot load game {game_id}: {e}") from e

            # Remove convenience fields that were added for UI
            metadata.pop("current_location_id", None)
            metadata.pop("current_act_id", None)

            # Reconstruct GameState from the loaded parts. Metadata are unpacked automatically. Rest is separately loaded
            game_state = GameState(
                **metadata,  # Unpack all metadata fields automatically
                character=character,
                scenario_instance=scenario_instance,
                conversation_history=[],
                game_events=[],
                npcs=[],
                monsters=[],
            )

            # Load remaining components
            game_state.conversation_history = self._load_conversation_history(save_dir)
            game_state.game_events = self._load_game_events(save_dir)
            game_state.npcs = self._load_npc_instances(save_dir)
            game_state.monsters = self._load_monster_instances(save_dir)

            # Load combat if exists
            if (save_dir / "combat.json").exists():
                game_state.combat = self._load_combat(save_dir)

            return game_state

        except Exception as e:
            raise RuntimeError(f"Failed to load game {scenario_id}/{game_id}: {e}") from e

    def list_saved_games(self, scenario_id: str | None = None) -> list[tuple[str, str, datetime]]:
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

    def _save_metadata(self, save_dir: Path, game_state: GameState) -> None:
        """Save game metadata by serializing the GameState model directly."""
        # Exclude large lists that are saved in separate files.
        metadata_dump = game_state.model_dump(
            exclude={
                "character",
                "npcs",
                "monsters",
                "scenario_instance",
                "conversation_history",
                "game_events",
                "combat",
            },
            mode="json",
        )

        # Add convenience fields for UI access
        metadata_dump["current_location_id"] = game_state.scenario_instance.current_location_id

        with open(save_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata_dump, f, indent=2, default=str)

    def _save_instances(self, save_dir: Path, game_state: GameState) -> None:
        """Save instances (character, scenario, npcs)."""
        inst_dir = save_dir / "instances"
        npcs_dir = inst_dir / "npcs"
        npcs_dir.mkdir(parents=True, exist_ok=True)

        with open(inst_dir / "character.json", "w", encoding="utf-8") as f:
            f.write(game_state.character.model_dump_json(indent=2))

        with open(inst_dir / "scenario.json", "w", encoding="utf-8") as f:
            f.write(game_state.scenario_instance.model_dump_json(indent=2))

        for npc in game_state.npcs:
            file_path = npcs_dir / f"{npc.instance_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(npc.model_dump_json(indent=2))

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

    def _save_monster_instances(self, save_dir: Path, monsters: list[MonsterInstance]) -> None:
        """Save MonsterInstances under instances/monsters."""
        monsters_dir = save_dir / "instances" / "monsters"
        monsters_dir.mkdir(parents=True, exist_ok=True)

        # Get current saved monster files
        existing_monster_files = set(monsters_dir.glob("*.json")) if monsters_dir.exists() else set()

        # Track which files we're keeping
        active_monster_files = set()

        # Save alive monsters
        for monster in monsters:
            file_path = monsters_dir / f"{monster.instance_id}.json"
            active_monster_files.add(file_path)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(monster.model_dump_json(indent=2))

        # Clean up dead monster files
        dead_monster_files = existing_monster_files - active_monster_files
        for dead_file in dead_monster_files:
            dead_file.unlink()
            logger.debug(f"Removed dead monster file: {dead_file.name}")

    def _save_combat(self, save_dir: Path, combat: CombatState) -> None:
        """Save combat state."""
        with open(save_dir / "combat.json", "w", encoding="utf-8") as f:
            f.write(combat.model_dump_json(indent=2))

    def _load_metadata(self, save_dir: Path) -> dict[str, Any]:
        """Load game metadata.

        Returns dict from JSON - proper typing is handled by the caller.

        Raises:
            FileNotFoundError: If metadata.json is missing (save corrupted)
            ValueError: If metadata.json is corrupted or invalid
        """
        file_path = save_dir / "metadata.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing metadata.json in {save_dir}. Save is corrupted.")
        try:
            with open(file_path, encoding="utf-8") as f:
                # json.load returns Any, which is what we need for metadata
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Corrupted metadata.json in {save_dir}: {e}") from e

    def _load_character_instance(self, save_dir: Path) -> CharacterInstance:
        """Load character instance.

        Raises:
            FileNotFoundError: If character.json is missing (save corrupted)
            ValueError: If character.json is corrupted or invalid
        """
        file_path = save_dir / "instances" / "character.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing character.json in {save_dir}. Save is corrupted.")
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return CharacterInstance(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Corrupted character.json in {save_dir}: {e}") from e

    def _load_scenario_instance(self, save_dir: Path) -> ScenarioInstance:
        """Load scenario instance from save directory.

        Raises:
            FileNotFoundError: If scenario.json is missing (save corrupted)
            ValueError: If scenario.json is corrupted or invalid
        """
        file_path = save_dir / "instances" / "scenario.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing scenario.json in {save_dir}. Save is corrupted.")
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return ScenarioInstance(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Corrupted scenario.json in {save_dir}: {e}") from e

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

    def _load_npc_instances(self, save_dir: Path) -> list[NPCInstance]:
        """Load NPC instances."""
        npcs_dir = save_dir / "instances" / "npcs"
        if not npcs_dir.exists():
            return []

        npcs: list[NPCInstance] = []
        for file_path in sorted(npcs_dir.glob("*.json")):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            npcs.append(NPCInstance(**data))
        return npcs

    def _load_monster_instances(self, save_dir: Path) -> list[MonsterInstance]:
        """Load MonsterInstances from instances/monsters."""
        monsters_dir = save_dir / "instances" / "monsters"
        if not monsters_dir.exists():
            return []

        monsters: list[MonsterInstance] = []
        for file_path in sorted(monsters_dir.glob("*.json")):
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            monsters.append(MonsterInstance(**data))
        return monsters

    def _load_combat(self, save_dir: Path) -> CombatState:
        """Load combat state.

        Returns empty CombatState if file doesn't exist (combat not active).

        Raises:
            ValueError: If combat.json exists but is corrupted
        """
        file_path = save_dir / "combat.json"
        if not file_path.exists():
            return CombatState()

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return CombatState(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Corrupted combat.json in {save_dir}: {e}") from e
