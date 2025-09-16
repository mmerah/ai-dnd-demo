"""Unit tests for `GameService`."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, create_autospec

import pytest

from app.interfaces.services.game import (
    IGameFactory,
    IGameStateManager,
    IPreSaveSanitizer,
    ISaveManager,
)
from app.models.character import CharacterSheet
from app.models.game_state import GameState
from app.services.game.game_service import GameService


class TestGameService:
    """Exercise the orchestration logic on `GameService`."""

    def setup_method(self) -> None:
        self.save_manager = create_autospec(ISaveManager, instance=True)
        self.pre_save_sanitizer = create_autospec(IPreSaveSanitizer, instance=True)
        self.game_state_manager = create_autospec(IGameStateManager, instance=True)
        self.game_factory = create_autospec(IGameFactory, instance=True)

        self.service = GameService(
            save_manager=self.save_manager,
            pre_save_sanitizer=self.pre_save_sanitizer,
            game_state_manager=self.game_state_manager,
            game_factory=self.game_factory,
        )

    @staticmethod
    def _make_game_state(game_id: str = "game-123", scenario_id: str = "scenario-001") -> GameState:
        state = MagicMock(spec=GameState)
        state.game_id = game_id
        state.scenario_id = scenario_id
        return state

    def test_initialize_game_creates_and_saves_state(self) -> None:
        game_state = self._make_game_state()
        self.game_factory.initialize_game.return_value = game_state
        self.save_manager.save_game.return_value = Path("/tmp/save-dir")

        result = self.service.initialize_game(
            character=MagicMock(spec=CharacterSheet),
            scenario_id="scenario-001",
            content_packs=["srd"],
        )

        assert result is game_state
        self.game_factory.initialize_game.assert_called_once()
        self.game_state_manager.store_game.assert_called_once_with(game_state)
        self.pre_save_sanitizer.sanitize.assert_called_once_with(game_state)
        self.save_manager.save_game.assert_called_once_with(game_state)

    def test_save_game_wraps_exceptions(self) -> None:
        game_state = self._make_game_state()
        self.save_manager.save_game.side_effect = RuntimeError("disk error")

        with pytest.raises(OSError) as exc:
            self.service.save_game(game_state)

        assert "Failed to save game" in str(exc.value)
        self.pre_save_sanitizer.sanitize.assert_called_once_with(game_state)

    def test_load_game_finds_scenario_and_stores_state(self) -> None:
        loaded_state = self._make_game_state(game_id="g2", scenario_id="scenario-002")
        self.save_manager.list_saved_games.return_value = [
            ("scenario-001", "g1", datetime.now()),
            ("scenario-002", "g2", datetime.now()),
        ]
        self.save_manager.load_game.return_value = loaded_state

        result = self.service.load_game("g2")

        assert result is loaded_state
        self.save_manager.load_game.assert_called_once_with("scenario-002", "g2")
        self.game_state_manager.store_game.assert_called_once_with(loaded_state)

    def test_load_game_raises_when_game_missing(self) -> None:
        self.save_manager.list_saved_games.return_value = [("scenario-001", "other", datetime.now())]

        with pytest.raises(FileNotFoundError):
            self.service.load_game("missing")

    def test_get_game_returns_cached_instance(self) -> None:
        cached_state = self._make_game_state()
        self.game_state_manager.get_game.return_value = cached_state

        result = self.service.get_game("game-123")

        assert result is cached_state
        self.save_manager.list_saved_games.assert_not_called()

    def test_list_saved_games_skips_corrupted_entries(self) -> None:
        good_state = self._make_game_state("g1", "scenario-001")
        self.save_manager.list_saved_games.return_value = [
            ("scenario-001", "g1", datetime.now()),
            ("scenario-002", "g2", datetime.now()),
        ]
        self.save_manager.load_game.side_effect = [good_state, RuntimeError("bad data")]

        result = self.service.list_saved_games()

        assert result == [good_state]
        assert self.save_manager.load_game.call_count == 2
