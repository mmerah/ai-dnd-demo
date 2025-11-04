"""Agent selection step for orchestration pipeline."""

import logging

from app.agents.core.types import AgentType
from app.models.game_state import GameState
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class SelectAgent:
    """Select the appropriate agent type based on game_state.active_agent."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Select the agent type based on game state."""
        agent_type = self._select_agent(ctx.game_state)

        logger.info("Selected agent: %s (from game_state.active_agent)", agent_type.value)

        updated_ctx = ctx.with_updates(selected_agent_type=agent_type)
        return StepResult.continue_with(updated_ctx)

    def _select_agent(self, game_state: GameState) -> AgentType:
        """Select the active agent type based on game state."""
        return game_state.active_agent
