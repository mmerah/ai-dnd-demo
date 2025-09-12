"""Summarizer agent for context bridging between narrative and combat agents."""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from pydantic_ai import Agent

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.prompts import SUMMARIZER_SYSTEM_PROMPT
from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState
from app.services.ai.debug_logger import AgentDebugLogger

logger = logging.getLogger(__name__)


@dataclass
class SummarizerAgent(BaseAgent):
    """Agent for summarizing context during agent transitions."""

    agent: Agent[None, str]
    context_service: IContextService
    debug_logger: AgentDebugLogger | None = None

    def get_required_tools(self) -> list[ToolFunction]:
        """Summarizer doesn't need tools - it just summarizes text."""
        return []

    async def _summarize_with_retry(self, prompt: str, fallback: str, warn_label: str) -> str:
        """Run the summarizer up to 2 times and return non-empty output or fallback.

        Args:
            prompt: The prompt to send to the summarizer model
            fallback: Fallback string if both attempts fail or are empty
            warn_label: Context label to include in warnings (e.g., "combat start")
        """
        for attempt in range(2):
            try:
                result = await self.agent.run(prompt)
                output = (result.output or "").strip()
                if output:
                    return output
                raise ValueError("Empty model response")
            except Exception as e:
                logger.warning(f"Summarization attempt {attempt + 1} failed ({warn_label}): {e}")
        return fallback

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
            + f"Game context:\n{context_text}\n\n"
            + narrative_block
            + "\n\nFocus on: How combat started, current environment, and any tactical considerations."
        )

        if self.debug_logger:
            self.debug_logger.log_agent_call(
                agent_type=AgentType.SUMMARIZER,
                game_id=game_state.game_id,
                system_prompt=SUMMARIZER_SYSTEM_PROMPT,
                conversation_history=[],
                user_prompt=prompt,
                context=context_text,
            )

        return await self._summarize_with_retry(
            prompt,
            fallback="Combat has begun after recent events.",
            warn_label="combat start",
        )

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
            + f"Game context:\n{context_text}\n\n"
            + combat_block
            + "\n\nFocus on: Combat outcome, casualties, loot gained, and story implications. Keep in mind that the combat has ended."
        )

        if self.debug_logger:
            self.debug_logger.log_agent_call(
                agent_type=AgentType.SUMMARIZER,
                game_id=game_state.game_id,
                system_prompt=SUMMARIZER_SYSTEM_PROMPT,
                conversation_history=[],
                user_prompt=prompt,
                context=context_text,
            )

        return await self._summarize_with_retry(
            prompt,
            fallback="Combat has ended with the party victorious.",
            warn_label="combat end",
        )

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
