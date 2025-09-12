"""Pre-save sanitization to keep SaveManager free of inline mutations."""

import logging

from app.interfaces.services.game import IPreSaveSanitizer
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class PreSaveSanitizer(IPreSaveSanitizer):
    """Sanitize game state before persistence.

    Responsibilities:
    - Remove dead monsters from game_state to avoid persisting stale entities.
    - Future: normalize/clean transient fields prior to save.
    """

    def sanitize(self, game_state: GameState) -> None:
        initial_monster_count = len(game_state.monsters)
        game_state.monsters = [m for m in game_state.monsters if m.is_alive()]
        if initial_monster_count != len(game_state.monsters):
            logger.debug(
                "PreSaveSanitizer: removed %d dead monsters before saving game %s",
                initial_monster_count - len(game_state.monsters),
                game_state.game_id,
            )
