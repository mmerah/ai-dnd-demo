"""Step to reload game state from the game service."""

import logging

from app.interfaces.services.game import IGameService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class ReloadState:
    """Reload the game state to get changes made by event handlers.

    This step reloads the game state from the game service to ensure the context
    has the latest state, including any mutations made by event handlers during
    agent execution or tool calls.

    This step fails fast - if reload fails, it raises an exception rather than
    continuing with stale state.

    Reload checkpoints (from orchestrator):
    - Line 159: After agent execution
    - Line 167: After combat start handling
    - Line 175: After combat continuation
    - Line 283: Before combat continuation check
    - Line 326: Before narrative aftermath
    """

    def __init__(self, game_service: IGameService):
        """Initialize the step with required services.

        Args:
            game_service: Service for loading game state
        """
        self.game_service = game_service

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Reload game state and update context.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with updated game_state in context

        Raises:
            Exception: If game state reload fails
        """
        old_state = ctx.game_state

        # Reload state - fail fast on error
        reloaded_state = self.game_service.get_game(ctx.game_id)

        # Log state changes for observability
        self._log_state_changes(old_state, reloaded_state)

        updated_ctx = ctx.with_updates(game_state=reloaded_state)
        return StepResult.continue_with(updated_ctx)

    def _log_state_changes(self, old_state, new_state) -> None:  # type: ignore[no-untyped-def]
        """Log significant state changes for observability.

        Args:
            old_state: State before reload
            new_state: State after reload
        """
        # Combat state changes
        if old_state.combat.is_active != new_state.combat.is_active:
            logger.info(
                "Combat state changed: %s → %s (game_id=%s)",
                "active" if old_state.combat.is_active else "inactive",
                "active" if new_state.combat.is_active else "inactive",
                new_state.game_id,
            )

        # Round changes (only log if combat is active)
        if new_state.combat.is_active and old_state.combat.round_number != new_state.combat.round_number:
            logger.info(
                "Combat round changed: %d → %d (game_id=%s)",
                old_state.combat.round_number,
                new_state.combat.round_number,
                new_state.game_id,
            )

        # Turn changes (only log if combat is active)
        if new_state.combat.is_active:
            old_turn = old_state.combat.get_current_turn()
            new_turn = new_state.combat.get_current_turn()

            old_entity_id = old_turn.entity_id if old_turn else None
            new_entity_id = new_turn.entity_id if new_turn else None

            if old_entity_id != new_entity_id:
                logger.info(
                    "Combat turn changed: %s → %s (game_id=%s)",
                    old_entity_id or "(none)",
                    new_entity_id or "(none)",
                    new_state.game_id,
                )
