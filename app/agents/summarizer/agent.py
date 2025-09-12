"""Summarizer agent for context bridging between narrative and combat agents."""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from pydantic_ai import Agent

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


@dataclass
class SummarizerAgent(BaseAgent):
    """Agent for summarizing context during agent transitions."""

    agent: Agent[None, str]
    context_service: IContextService

    def get_required_tools(self) -> list[ToolFunction]:
        """Summarizer doesn't need tools - it just summarizes text."""
        return []

    async def summarize_for_combat(self, game_state: GameState) -> str:
        """Create a summary when transitioning from narrative to combat.

        Args:
            game_state: Current game state

        Returns:
            Brief summary of narrative context for combat agent
        """
        # Build structured game context (ensures combat state is represented)
        context_text = self.context_service.build_context(game_state, AgentType.SUMMARIZER)

        # Build recent narrative from conversation history (if available)
        recent_messages = game_state.get_messages_for_agent(AgentType.NARRATIVE)
        narrative_block = (
            "Recent narrative context:\n" + "\n".join(f"- {msg.role}: {msg.content}" for msg in recent_messages)
            if recent_messages
            else ""
        )

        prompt = (
            "Summarize this context for combat in 2-3 sentences:\n"
            + (f"Game context:\n{context_text}\n\n" if context_text else "")
            + narrative_block
            + "\n\nFocus on: How combat started, current environment, and any tactical considerations."
        )

        try:
            # Summarizer runs without dependencies
            result = await self.agent.run(prompt)
            return result.output
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Combat has begun after recent events."

    async def summarize_combat_end(self, game_state: GameState) -> str:
        """Create a summary when transitioning from combat to narrative.

        Args:
            game_state: Current game state

        Returns:
            Brief summary of combat outcome for narrative agent
        """
        # Build structured game context (ensures final combat state is represented)
        context_text = self.context_service.build_context(game_state, AgentType.SUMMARIZER)

        # Build combat messages block
        recent_messages = game_state.get_messages_for_combat(game_state.combat.combat_occurrence)
        combat_block = (
            "Combat sequence:\n" + "\n".join(f"- {msg.role}: {msg.content}" for msg in recent_messages)
            if recent_messages
            else ""
        )

        prompt = (
            "Summarize this combat for the narrative in 2-3 sentences:\n"
            + (f"Game context:\n{context_text}\n\n" if context_text else "")
            + combat_block
            + "\n\nFocus on: Combat outcome, casualties, loot gained, and story implications. Keep in mind that the combat has ended."
        )

        try:
            # Summarizer runs without dependencies
            result = await self.agent.run(prompt)
            return result.output
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Combat has ended with the party victorious."

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """Process method required by BaseAgent but not used for summarizer."""
        # This agent doesn't process user prompts directly
        # Make it an async generator to satisfy the type signature
        raise NotImplementedError("Summarizer agent doesn't process user prompts directly")
        yield  # type: ignore[unreachable]
