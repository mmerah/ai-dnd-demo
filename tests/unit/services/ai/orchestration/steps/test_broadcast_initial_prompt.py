"""Tests for BroadcastInitialPrompt step."""

from unittest.mock import AsyncMock, create_autospec

import pytest

from app.interfaces.events import IEventBus
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome
from app.services.ai.orchestration.steps.broadcast_initial_prompt import BroadcastInitialPrompt
from tests.factories import make_game_state


class TestBroadcastInitialPrompt:
    """Tests for BroadcastInitialPrompt step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.event_bus = create_autospec(IEventBus, instance=True)
        self.event_bus.submit_and_wait = AsyncMock()
        self.step = BroadcastInitialPrompt(self.event_bus)

    @pytest.mark.asyncio
    async def test_broadcasts_prompt_as_system_message(self) -> None:
        """Test that step broadcasts prompt as system message."""
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt="Combat begins! Roll initiative.",
        )

        result = await self.step.run(ctx)

        # Verify event bus was called
        assert self.event_bus.submit_and_wait.called
        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert len(call_args) == 1
        assert "[Combat System:" in call_args[0].content
        assert "Combat begins! Roll initiative." in call_args[0].content

        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_handles_empty_prompt_with_warning(self) -> None:
        """Test that step handles empty prompt with warning."""
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt="",
        )

        result = await self.step.run(ctx)

        # Should not call event bus for empty prompt
        assert not self.event_bus.submit_and_wait.called
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_uses_correct_message_format(self) -> None:
        """Test that step uses correct [Combat System: ...] format."""
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt="Test prompt",
        )

        await self.step.run(ctx)

        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert call_args[0].content == "[Combat System: Test prompt]"

    @pytest.mark.asyncio
    async def test_broadcasts_multiline_prompt(self) -> None:
        """Test that step handles multiline prompts correctly."""
        multiline_prompt = "Combat begins!\nRoll for initiative.\nEnemies: 2 goblins."
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt=multiline_prompt,
        )

        await self.step.run(ctx)

        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert multiline_prompt in call_args[0].content

    @pytest.mark.asyncio
    async def test_marks_broadcast_as_complete(self) -> None:
        """Test that broadcast command is marked as complete."""
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt="Test prompt",
        )

        await self.step.run(ctx)

        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert call_args[0].is_complete is True

    @pytest.mark.asyncio
    async def test_uses_correct_game_id(self) -> None:
        """Test that broadcast uses correct game_id from context."""
        ctx = OrchestrationContext(
            user_message="Attack!",
            game_state=self.game_state,
            current_prompt="Test prompt",
        )

        await self.step.run(ctx)

        call_args = self.event_bus.submit_and_wait.call_args[0][0]
        assert call_args[0].game_id == "test-game"
