"""Agent selection step for orchestration pipeline."""

import logging

from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class SelectAgent:
    """Step that selects the appropriate agent type based on game state.

    This step uses a simple selection strategy: it reads the game_state.active_agent
    field to determine which agent should handle the current request.

    The active_agent field is typically:
    - AgentType.NARRATIVE when not in combat
    - AgentType.COMBAT when combat is active
    - AgentType.NPC when in a dialogue session
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Select the agent type based on game state.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with selected_agent_type updated in context
        """
        agent_type = self._select_agent(ctx.game_state)

        logger.info(
            "SelectAgent: game_id=%s, selected_agent=%s (from game_state.active_agent)",
            ctx.game_id,
            agent_type.value,
        )

        updated_ctx = ctx.with_updates(selected_agent_type=agent_type)
        return StepResult.continue_with(updated_ctx)

    def _select_agent(self, game_state: GameState) -> AgentType:
        """Select the active agent type based on the current game state.

        Args:
            game_state: Current game state

        Returns:
            The agent type that should handle this request
        """
        return game_state.active_agent
