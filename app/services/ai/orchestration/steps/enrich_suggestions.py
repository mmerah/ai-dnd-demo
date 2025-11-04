"""Step to enrich context with tool suggestions."""

import logging

from app.agents.core.base import BaseAgent
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.tool_suggestion import ToolSuggestions
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class EnrichContextWithToolSuggestions:
    """Enrich agent context with tool suggestions from ToolSuggestorAgent.

    This step calls the ToolSuggestorAgent to generate heuristic-based tool suggestions
    for the selected agent, then appends formatted suggestions to the context text.

    The step is designed to work with all agent types (NARRATIVE, COMBAT, NPC) and
    defaults to ON for all agents as per the plan.
    """

    def __init__(self, tool_suggestor_agent: BaseAgent):
        """Initialize the step with the tool suggestor agent.

        Args:
            tool_suggestor_agent: Agent that generates tool suggestions
        """
        self.tool_suggestor_agent = tool_suggestor_agent

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Enrich context with tool suggestions for the selected agent.

        Args:
            ctx: Current orchestration context with selected_agent_type

        Returns:
            StepResult with updated context_text

        Raises:
            ValueError: If agent type has not been selected yet
        """
        # Ensure agent type is selected (orchestrator line 132)
        agent_type = ctx.require_agent_type()

        logger.info(
            "EnrichContextWithToolSuggestions: game_id=%s, agent_type=%s, incoming_context_length=%d",
            ctx.game_id,
            agent_type.value,
            len(ctx.context_text),
        )

        # Build suggestion prompt (orchestrator line 133)
        tool_suggestions_prompt = f"TARGET_AGENT: {agent_type.value}\n\nUSER_PROMPT: {ctx.user_message}"

        # Call tool suggestor agent (orchestrator lines 134-139)
        suggestions_events: list[StreamEvent] = [
            event
            async for event in self.tool_suggestor_agent.process(
                tool_suggestions_prompt, ctx.game_state, context="", stream=False
            )
        ]

        # Extract suggestions from COMPLETE event (orchestrator lines 142-147)
        suggestions = ToolSuggestions(suggestions=[])
        if suggestions_events:
            for event in suggestions_events:
                if event.type == StreamEventType.COMPLETE and isinstance(event.content, ToolSuggestions):
                    suggestions = event.content
                    break

        logger.info(
            "EnrichContextWithToolSuggestions: Generated %d suggestions for agent_type=%s",
            len(suggestions.suggestions),
            agent_type.value,
        )

        # Enrich context with suggestions if any (orchestrator lines 150-152)
        updated_context_text = ctx.context_text
        if suggestions.suggestions:
            suggestions_text = suggestions.format_for_prompt()
            updated_context_text = f"{ctx.context_text}\n\n{suggestions_text}"

            logger.info(
                "EnrichContextWithToolSuggestions: Enriched context with %d suggestions, new_length=%d (was %d)",
                len(suggestions.suggestions),
                len(updated_context_text),
                len(ctx.context_text),
            )
        else:
            logger.info(
                "EnrichContextWithToolSuggestions: No suggestions to add, context_length=%d",
                len(ctx.context_text),
            )

        # Update context with enriched text
        updated_ctx = ctx.with_updates(context_text=updated_context_text)

        return StepResult.continue_with(updated_ctx)
