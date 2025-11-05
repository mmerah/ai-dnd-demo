"""Step to enrich context with tool suggestions."""

import logging

from app.agents.core.base import BaseAgent
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class EnrichContextWithToolSuggestions:
    """Enrich agent context with tool suggestions from ToolSuggestorAgent."""

    def __init__(self, tool_suggestor_agent: BaseAgent):
        """Initialize with tool suggestor agent."""
        self.tool_suggestor_agent = tool_suggestor_agent

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Enrich context with tool suggestions for the selected agent."""
        # Ensure agent type is selected
        agent_type = ctx.require_agent_type()

        # Build suggestion prompt
        tool_suggestions_prompt = f"TARGET_AGENT: {agent_type.value}\n\nUSER_PROMPT: {ctx.user_message}"

        # Call tool suggestor agent
        suggestions_events: list[StreamEvent] = [
            event
            async for event in self.tool_suggestor_agent.process(
                tool_suggestions_prompt, ctx.game_state, context="", stream=False
            )
        ]

        # Extract suggestions from COMPLETE event
        suggestions = ToolSuggestions(suggestions=[])
        if suggestions_events:
            for event in suggestions_events:
                if event.type == StreamEventType.COMPLETE and isinstance(event.content, ToolSuggestions):
                    suggestions = event.content
                    break

        # Enrich context with suggestions if any
        updated_context_text = ctx.context_text
        if suggestions.suggestions:
            suggestions_text = suggestions.format_for_prompt()
            updated_context_text = f"{ctx.context_text}\n\n{suggestions_text}"
            logger.info("Enriched %s context with %d suggestions", agent_type.value, len(suggestions.suggestions))
        else:
            logger.debug("No tool suggestions generated for %s", agent_type.value)

        # Update context with enriched text
        updated_ctx = ctx.with_updates(context_text=updated_context_text)

        return StepResult.continue_with(updated_ctx)
