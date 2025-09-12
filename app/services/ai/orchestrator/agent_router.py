"""Agent selection helper for the orchestrator."""

from app.agents.core.types import AgentType
from app.models.game_state import GameState


def select(game_state: GameState) -> AgentType:
    """Select the active agent type based on the current game state."""
    return game_state.active_agent
