"""Unit tests for `PreSaveSanitizer`."""

from unittest.mock import MagicMock

from app.models.game_state import GameState
from app.models.instances.monster_instance import MonsterInstance
from app.services.game.pre_save_sanitizer import PreSaveSanitizer


class TestPreSaveSanitizer:
    """Ensure sanitization strips dead monsters."""

    def setup_method(self) -> None:
        self.sanitizer = PreSaveSanitizer()

    def test_sanitize_removes_dead_monsters(self) -> None:
        alive = MagicMock(spec=MonsterInstance)
        alive.is_alive.return_value = True
        dead = MagicMock(spec=MonsterInstance)
        dead.is_alive.return_value = False

        game_state = MagicMock(spec=GameState)
        game_state.monsters = [alive, dead]
        game_state.game_id = "g1"

        self.sanitizer.sanitize(game_state)

        assert game_state.monsters == [alive]
