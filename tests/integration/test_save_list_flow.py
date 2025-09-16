"""Integration test for save listing and loading flow."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from app.container import Container
from tests.factories import make_character_sheet, make_location, make_scenario


class TestSaveListFlow:
    """Ensure saves written via SaveManager are visible through GameService."""

    def setup_method(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.container = Container()
        self.save_path = self.temp_dir / "saves"
        self.save_path.mkdir()

        self.scenario = make_scenario(
            scenario_id="integration-scenario",
            title="Integration Scenario",
            description="Used to confirm game listing.",
            starting_location_id="start",
            locations=[
                make_location(
                    location_id="start",
                    name="Start",
                    description="Starting point",
                )
            ],
        )

    def teardown_method(self) -> None:
        for path in sorted(self.temp_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.temp_dir.rmdir()

    def test_save_and_list(self) -> None:
        with (
            patch.object(self.container.path_resolver, "saves_dir", self.save_path, create=True),
            patch.object(self.container.scenario_service, "get_scenario", return_value=self.scenario),
        ):
            game_service = self.container.game_service

            character = make_character_sheet(character_id="char-a", name="Char A")
            game_state_a = game_service.initialize_game(
                character=character,
                scenario_id=self.scenario.id,
                content_packs=["srd"],
            )

            character_b = make_character_sheet(character_id="char-b", name="Char B")
            game_state_b = game_service.initialize_game(
                character=character_b,
                scenario_id=self.scenario.id,
                content_packs=["srd"],
            )

            listed = game_service.list_saved_games()

            assert len(listed) == 2
            game_ids = {game.game_id for game in listed}
            assert {game_state_a.game_id, game_state_b.game_id} == game_ids

            reloaded = game_service.load_game(game_state_a.game_id)
            assert reloaded.character.sheet.name == character.name
