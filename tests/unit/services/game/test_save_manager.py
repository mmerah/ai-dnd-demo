"""Unit tests for `SaveManager`."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.models.game_state import GameEvent, GameEventType, GameState, Message, MessageRole
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.services.common.path_resolver import PathResolver
from app.services.game.save_manager import SaveManager
from tests.factories import (
    make_character_instance,
    make_character_sheet,
    make_location,
    make_monster_instance,
    make_monster_sheet,
    make_scenario,
)


class _TempPathResolver(PathResolver):
    """PathResolver that stores data under a temporary directory."""

    def __init__(self, root: Path):
        super().__init__(root_dir=root)


class TestSaveManager:
    """Exercise persistence behaviour of `SaveManager`."""

    def setup_method(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.path_resolver = _TempPathResolver(self.temp_dir)
        self.manager = SaveManager(self.path_resolver)

        sheet = make_character_sheet()
        self.character = make_character_instance(sheet=sheet, instance_id="char-1")

        start_location = make_location(
            location_id="town-square",
            name="Town Square",
            description="The bustling heart of town.",
        )
        scenario = make_scenario(
            scenario_id="sample-scenario",
            title="Sample Scenario",
            description="A scenario used for SaveManager tests.",
            starting_location_id=start_location.id,
            locations=[start_location],
        )
        self.scenario_instance = ScenarioInstance(
            instance_id="scn-1",
            template_id=scenario.id,
            sheet=scenario,
            current_location_id=start_location.id,
            current_act_id=scenario.progression.acts[0].id,
        )
        self.scenario_instance.location_states[start_location.id] = LocationState(location_id=start_location.id)

        self.game_state = GameState(
            game_id="game-123",
            character=self.character,
            npcs=[],
            monsters=[],
            scenario_id=scenario.id,
            scenario_title=scenario.title,
            scenario_instance=self.scenario_instance,
            content_packs=list(scenario.content_packs),
            location=start_location.name,
            conversation_history=[
                Message(role=MessageRole.DM, content="Welcome!"),
            ],
            game_events=[
                GameEvent(event_type=GameEventType.TOOL_CALL, tool_name="dice", parameters={}),
            ],
        )

    def teardown_method(self) -> None:
        for path in sorted(self.temp_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.temp_dir.rmdir()

    def test_save_and_load_round_trip(self) -> None:
        save_dir = self.manager.save_game(self.game_state)

        metadata_file = save_dir / "metadata.json"
        assert metadata_file.exists()

        loaded = self.manager.load_game(self.game_state.scenario_id, self.game_state.game_id)

        assert loaded.game_id == self.game_state.game_id
        assert loaded.character.sheet.name == self.character.sheet.name
        assert loaded.location == self.game_state.location
        assert loaded.conversation_history[0].content == self.game_state.conversation_history[0].content
        assert loaded.game_events[0].event_type == self.game_state.game_events[0].event_type

    def test_list_saved_games_returns_sorted_entries(self) -> None:
        self.manager.save_game(self.game_state)
        second_state = self.game_state.model_copy(deep=True)
        second_state.game_id = "game-456"
        self.manager.save_game(second_state)

        saves = self.manager.list_saved_games()

        assert len(saves) == 2
        # list_saved_games returns tuples sorted by last_saved desc
        assert saves[0][1] == second_state.game_id
        assert saves[1][1] == self.game_state.game_id

    def test_save_game_skips_dead_monsters_files(self) -> None:
        monster_sheet = make_monster_sheet(name="Wolf")
        monster = make_monster_instance(
            sheet=monster_sheet,
            instance_id="mon-1",
            current_location_id=self.scenario_instance.current_location_id,
            hp_current=0,
        )
        self.game_state.monsters = [monster]

        save_dir = self.manager.save_game(self.game_state)

        monsters_dir = save_dir / "instances" / "monsters"
        assert monsters_dir.exists()
        assert not any(monsters_dir.glob("*.json"))
