"""Tool Suggestor Agent for pre-flight tool recommendations."""

import logging
from collections.abc import AsyncIterator

from app.agents.core.base import BaseAgent, ToolFunction
from app.interfaces.services.ai import IToolSuggestionService
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestions

logger = logging.getLogger(__name__)


class ToolSuggestorAgent(BaseAgent):
    """Agent that suggests appropriate tools based on context and user prompt.

    This agent uses heuristic rules to suggest tools before the main agent runs.
    It implements BaseAgent for consistency and future LLM integration, but currently
    uses only heuristic-based suggestions.

    Note: The context parameter in process() is required by BaseAgent interface
    but unused by this agent since it only needs game_state and prompt for heuristics.
    """

    def __init__(self, suggestion_service: IToolSuggestionService) -> None:
        """Initialize the tool suggestor agent.

        Args:
            suggestion_service: Service for generating tool suggestions
        """
        self.suggestion_service = suggestion_service

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        context: str = "",
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        # Parse the structured prompt format
        try:
            lines = prompt.split("\n\n", 1)
            if len(lines) != 2:
                raise ValueError("Prompt must contain TARGET_AGENT and USER_PROMPT sections")

            target_agent_line = lines[0]
            user_prompt_line = lines[1]

            if not target_agent_line.startswith("TARGET_AGENT: "):
                raise ValueError("First section must start with 'TARGET_AGENT: '")

            if not user_prompt_line.startswith("USER_PROMPT: "):
                raise ValueError("Second section must start with 'USER_PROMPT: '")

            target_agent_type = target_agent_line.replace("TARGET_AGENT: ", "").strip()
            user_prompt = user_prompt_line.replace("USER_PROMPT: ", "").strip()

        except Exception as e:
            logger.error(f"Failed to parse tool suggestor prompt: {e}")
            # Return empty suggestions on parse error
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=ToolSuggestions(suggestions=[]),
            )
            return

        # Call the suggestion service
        try:
            suggestions = await self.suggestion_service.suggest_tools(
                game_state=game_state,
                prompt=user_prompt,
                agent_type=target_agent_type,
            )

            logger.info(
                f"Tool suggestor generated {len(suggestions.suggestions)} suggestions "
                f"for agent_type={target_agent_type}"
            )

            # Yield the suggestions as a complete event
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=suggestions,
            )

        except Exception as e:
            logger.error(f"Error generating tool suggestions: {e}", exc_info=True)
            # Return empty suggestions on error
            yield StreamEvent(
                type=StreamEventType.COMPLETE,
                content=ToolSuggestions(suggestions=[]),
            )
