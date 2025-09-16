"""Unit tests for `PreSaveSanitizer`."""

from unittest.mock import create_autospec

from app.models.game_state import GameState
from app.services.game.pre_save_sanitizer import PreSaveSanitizer
from tests.factories import make_monster_instance


class TestPreSaveSanitizer:
    """Ensure sanitization strips dead monsters."""

    def setup_method(self) -> None:
        self.sanitizer = PreSaveSanitizer()

    def test_sanitize_removes_dead_monsters(self) -> None:
        alive = make_monster_instance(hp_current=5)
        dead = make_monster_instance(instance_id="dead-1", hp_current=0)

        game_state = create_autospec(GameState, instance=True)
        game_state.monsters = [alive, dead]
        game_state.game_id = "g1"

        self.sanitizer.sanitize(game_state)

        assert game_state.monsters == [alive]
