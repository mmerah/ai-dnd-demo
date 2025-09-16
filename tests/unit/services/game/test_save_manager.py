"""Unit tests for `SaveManager`."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.models.game_state import GameEvent, GameEventType, GameState, Message, MessageRole
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.entity_state import EntityState, HitDice, HitPoints
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.services.common.path_resolver import PathResolver
from app.services.game.save_manager import SaveManager
from tests.factories import make_character_sheet, make_location, make_monster_sheet, make_scenario


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
        state = EntityState(
            abilities=sheet.starting_abilities,
            level=sheet.starting_level,
            experience_points=sheet.starting_experience_points,
            hit_points=HitPoints(current=10, maximum=12, temporary=0),
            hit_dice=HitDice(total=1, current=1, type="d10"),
            currency=sheet.starting_currency.model_copy(),
        )
        self.character = CharacterInstance(
            instance_id="char-1",
            template_id=sheet.id,
            sheet=sheet,
            state=state,
        )

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
        monster = MonsterInstance(
            instance_id="mon-1",
            template_id=monster_sheet.index,
            sheet=monster_sheet,
            state=EntityState(
                abilities=monster_sheet.abilities,
                level=1,
                experience_points=0,
                hit_points=HitPoints(current=0, maximum=monster_sheet.hit_points.maximum, temporary=0),
                hit_dice=HitDice(total=1, current=0, type="d8"),
                currency=self.character.state.currency.model_copy(),
            ),
            current_location_id=self.scenario_instance.current_location_id,
        )
        self.game_state.monsters = [monster]

        save_dir = self.manager.save_game(self.game_state)

        monsters_dir = save_dir / "instances" / "monsters"
        assert monsters_dir.exists()
        assert not any(monsters_dir.glob("*.json"))
