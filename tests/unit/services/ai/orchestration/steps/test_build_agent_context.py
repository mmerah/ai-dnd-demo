"""Tests for BuildAgentContext step."""

from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.interfaces.services.ai import IContextService
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.build_agent_context import BuildAgentContext
from tests.factories import make_game_state


class TestBuildAgentContext:
    """Tests for BuildAgentContext step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.context_service = create_autospec(IContextService, instance=True)
        self.step = BuildAgentContext(self.context_service)

    @pytest.mark.asyncio
    async def test_builds_context_for_agent_types(self) -> None:
        """Test building context for different agent types."""
        # Narrative
        self.context_service.build_context.return_value = "Narrative context"
        ctx = OrchestrationContext(
            user_message="I look around", game_state=self.game_state, selected_agent_type=AgentType.NARRATIVE
        )
        result = await self.step.run(ctx)
        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.context_text == "Narrative context"
        self.context_service.build_context.assert_called_once_with(self.game_state, AgentType.NARRATIVE)

        # Combat
        self.context_service.reset_mock()
        self.context_service.build_context.return_value = "Combat context"
        ctx = OrchestrationContext(
            user_message="I attack", game_state=self.game_state, selected_agent_type=AgentType.COMBAT
        )
        result = await self.step.run(ctx)
        assert result.context.context_text == "Combat context"
        self.context_service.build_context.assert_called_once_with(self.game_state, AgentType.COMBAT)

    @pytest.mark.asyncio
    async def test_requires_agent_type_selected(self) -> None:
        """Test that step requires agent type to be selected first."""
        ctx = OrchestrationContext(user_message="I look around", game_state=self.game_state)

        with pytest.raises(ValueError, match="Agent type not selected"):
            await self.step.run(ctx)
