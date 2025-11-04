"""Step to reload game state from the game service."""

import logging

from app.interfaces.services.game import IGameService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ReloadState:
    """Reload game state to get changes made by event handlers.

    Fails fast if reload fails (no fallback to stale state).
    """

    def __init__(self, game_service: IGameService):
        """Initialize with game service."""
        self.game_service = game_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Reload game state and update context."""
        old_state = ctx.game_state
        reloaded_state = self.game_service.get_game(ctx.game_id)

        # Log significant state changes
        self._log_state_changes(old_state, reloaded_state)

        updated_ctx = ctx.with_updates(game_state=reloaded_state)
        return StepResult.continue_with(updated_ctx)

    def _log_state_changes(self, old_state, new_state) -> None:  # type: ignore[no-untyped-def]
        """Log significant state changes."""
        # Combat state changes
        if old_state.combat.is_active != new_state.combat.is_active:
            logger.info(
                "Combat state: %s → %s",
                "active" if old_state.combat.is_active else "inactive",
                "active" if new_state.combat.is_active else "inactive",
            )

        # Round changes (only log if combat is active)
        if new_state.combat.is_active and old_state.combat.round_number != new_state.combat.round_number:
            logger.info("Combat round: %d → %d", old_state.combat.round_number, new_state.combat.round_number)

        # Turn changes (only log if combat is active)
        if new_state.combat.is_active:
            old_turn = old_state.combat.get_current_turn()
            new_turn = new_state.combat.get_current_turn()

            old_entity_id = old_turn.entity_id if old_turn else None
            new_entity_id = new_turn.entity_id if new_turn else None

            if old_entity_id != new_entity_id:
                logger.info("Combat turn: %s → %s", old_entity_id or "(none)", new_entity_id or "(none)")
