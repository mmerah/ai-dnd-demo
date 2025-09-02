"""Agent orchestrator to route requests between specialized agents."""

from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent
from app.interfaces.services import IGameService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState


class AgentOrchestrator:
    """Coordinates which agent should handle a given turn."""

    def __init__(self, narrative_agent: BaseAgent) -> None:
        self.narrative_agent = narrative_agent

    def _select_agent(self, game_state: GameState) -> BaseAgent:
        """Select the appropriate agent based on game state"""
        # MVP: always route to narrative agent; extend here in future
        return self.narrative_agent

    async def process(
        self,
        user_message: str,
        game_state: GameState,
        game_service: IGameService,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        agent = self._select_agent(game_state)
        async for event in agent.process(user_message, game_state, game_service, stream=stream):
            yield event
