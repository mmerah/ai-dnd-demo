"""Tests for EnrichContextWithToolSuggestions step."""

from collections.abc import AsyncIterator

import pytest

from app.agents.core.base import BaseAgent, ToolFunction
from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent, StreamEventType
from app.models.game_state import GameState
from app.models.tool_suggestion import ToolSuggestion, ToolSuggestions
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.enrich_suggestions import (
    EnrichContextWithToolSuggestions,
)
from tests.factories import make_game_state


class _StubToolSuggestorAgent(BaseAgent):
    """Stub agent that returns predefined suggestions."""

    def __init__(self, suggestions: ToolSuggestions):
        self.suggestions = suggestions
        self.call_count = 0
        self.last_prompt: str | None = None
        self.last_game_state: GameState | None = None

    def get_required_tools(self) -> list[ToolFunction]:
        return []

    async def process(
        self,
        prompt: str,
        game_state: GameState,
        context: str = "",
        stream: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_game_state = game_state

        yield StreamEvent(
            type=StreamEventType.COMPLETE,
            content=self.suggestions,
        )


class TestEnrichContextWithToolSuggestions:
    """Tests for EnrichContextWithToolSuggestions step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")

    @pytest.mark.asyncio
    async def test_enriches_context_with_suggestions(self) -> None:
        """Test that suggestions are appended to context_text."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(
                    tool_name="roll_dice",
                    reason="Player wants to check",
                    confidence=0.85,
                ),
            ]
        )

        stub_agent = _StubToolSuggestorAgent(suggestions)
        step = EnrichContextWithToolSuggestions(stub_agent)

        ctx = OrchestrationContext(
            user_message="I search for traps",
            game_state=self.game_state,
            selected_agent_type=AgentType.NARRATIVE,
            context_text="Initial context.",
        )

        result = await step.run(ctx)

        # Verify outcome
        assert result.outcome == OrchestrationOutcome.CONTINUE

        # Verify context enriched
        assert "Initial context." in result.context.context_text
        assert "## Tool Suggestions" in result.context.context_text
        assert result.context.context_text != ctx.context_text

    @pytest.mark.asyncio
    async def test_no_enrichment_when_empty_suggestions(self) -> None:
        """Test that empty suggestions don't modify context_text."""
        empty_suggestions = ToolSuggestions(suggestions=[])
        stub_agent = _StubToolSuggestorAgent(empty_suggestions)
        step = EnrichContextWithToolSuggestions(stub_agent)

        ctx = OrchestrationContext(
            user_message="I look around",
            game_state=self.game_state,
            selected_agent_type=AgentType.NARRATIVE,
            context_text="Original context.",
        )

        result = await step.run(ctx)

        # Context unchanged
        assert result.context.context_text == "Original context."
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_builds_correct_prompt_format(self) -> None:
        """Test that ToolSuggestorAgent receives correct prompt format."""
        stub_agent = _StubToolSuggestorAgent(ToolSuggestions(suggestions=[]))
        step = EnrichContextWithToolSuggestions(stub_agent)

        ctx = OrchestrationContext(
            user_message="I attack the goblin",
            game_state=self.game_state,
            selected_agent_type=AgentType.COMBAT,
        )

        await step.run(ctx)

        # Verify prompt format (orchestrator:133)
        assert stub_agent.last_prompt == "TARGET_AGENT: combat\n\nUSER_PROMPT: I attack the goblin"
        assert stub_agent.last_game_state is self.game_state

    @pytest.mark.asyncio
    async def test_works_with_all_agent_types(self) -> None:
        """Test that enrichment works for NARRATIVE, COMBAT, and NPC agents."""
        for agent_type in [AgentType.NARRATIVE, AgentType.COMBAT, AgentType.NPC]:
            stub_agent = _StubToolSuggestorAgent(ToolSuggestions(suggestions=[]))
            step = EnrichContextWithToolSuggestions(stub_agent)

            ctx = OrchestrationContext(
                user_message="Test message",
                game_state=self.game_state,
                selected_agent_type=agent_type,
            )

            result = await step.run(ctx)

            # Verify prompt includes correct agent type
            expected_prefix = f"TARGET_AGENT: {agent_type.value}\n\n"
            assert stub_agent.last_prompt is not None
            assert stub_agent.last_prompt.startswith(expected_prefix)
            assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_requires_agent_type_selected(self) -> None:
        """Test that step raises if agent type not selected."""
        stub_agent = _StubToolSuggestorAgent(ToolSuggestions(suggestions=[]))
        step = EnrichContextWithToolSuggestions(stub_agent)

        ctx = OrchestrationContext(
            user_message="Test",
            game_state=self.game_state,
        )

        with pytest.raises(ValueError, match="Agent type not selected"):
            await step.run(ctx)

    @pytest.mark.asyncio
    async def test_extracts_suggestions_from_complete_event(self) -> None:
        """Test that suggestions are extracted from COMPLETE event only."""

        class _MultiEventAgent(BaseAgent):
            """Agent that yields multiple events."""

            def get_required_tools(self) -> list[ToolFunction]:
                return []

            async def process(
                self, prompt: str, game_state: GameState, context: str = "", stream: bool = True
            ) -> AsyncIterator[StreamEvent]:
                # Yield non-COMPLETE events first
                yield StreamEvent(type=StreamEventType.THINKING, content="thinking")
                yield StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="chunk")
                # Then COMPLETE with suggestions
                yield StreamEvent(
                    type=StreamEventType.COMPLETE,
                    content=ToolSuggestions(
                        suggestions=[ToolSuggestion(tool_name="final", reason="final", confidence=0.9)]
                    ),
                )

        step = EnrichContextWithToolSuggestions(_MultiEventAgent())

        ctx = OrchestrationContext(
            user_message="Test",
            game_state=self.game_state,
            selected_agent_type=AgentType.NARRATIVE,
            context_text="Context",
        )

        result = await step.run(ctx)

        # Suggestions enriched context
        assert "## Tool Suggestions" in result.context.context_text
        assert "final" in result.context.context_text
