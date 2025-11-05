"""Tests for Step protocol, StepResult, and OrchestrationOutcome."""

import pytest

from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import OrchestrationOutcome, StepResult
from tests.factories import make_game_state


class TestStepResult:
    """Tests for StepResult dataclass."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    def test_step_result_creation(self) -> None:
        """Test creating a StepResult directly."""
        result = StepResult(outcome=OrchestrationOutcome.CONTINUE, context=self.ctx, reason="Testing")

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context is self.ctx
        assert result.reason == "Testing"

    def test_step_result_without_reason(self) -> None:
        """Test creating a StepResult without optional reason."""
        result = StepResult(outcome=OrchestrationOutcome.CONTINUE, context=self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context is self.ctx
        assert result.reason is None

    def test_continue_with_factory(self) -> None:
        """Test StepResult.continue_with factory method."""
        result = StepResult.continue_with(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context is self.ctx
        assert result.reason is None

    def test_halt_factory(self) -> None:
        """Test StepResult.halt factory method."""
        result = StepResult.halt(self.ctx, reason="NPC dialogue completed")

        assert result.outcome == OrchestrationOutcome.HALT
        assert result.context is self.ctx
        assert result.reason == "NPC dialogue completed"

    def test_branch_factory(self) -> None:
        """Test StepResult.branch factory method."""
        result = StepResult.branch(self.ctx, reason="Conditional execution")

        assert result.outcome == OrchestrationOutcome.BRANCH
        assert result.context is self.ctx
        assert result.reason == "Conditional execution"


class TestStepProtocol:
    """Tests for Step protocol compliance."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_step_protocol_simple_implementation(self) -> None:
        """Test that a simple class can implement Step protocol."""

        class SimpleStep:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                return StepResult.continue_with(ctx)

        step = SimpleStep()
        result = await step.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context is self.ctx

    @pytest.mark.asyncio
    async def test_step_protocol_with_context_modification(self) -> None:
        """Test step that modifies context."""

        class ModifyingStep:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                updated_ctx = ctx.with_updates(context_text="Modified context")
                return StepResult.continue_with(updated_ctx)

        step = ModifyingStep()
        result = await step.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert result.context.context_text == "Modified context"
        # Original context unchanged
        assert self.ctx.context_text == ""

    @pytest.mark.asyncio
    async def test_step_protocol_with_halt(self) -> None:
        """Test step that halts pipeline."""

        class HaltingStep:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                return StepResult.halt(ctx, reason="Early exit required")

        step = HaltingStep()
        result = await step.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.HALT
        assert result.reason == "Early exit required"

    @pytest.mark.asyncio
    async def test_step_protocol_with_state_inspection(self) -> None:
        """Test step that inspects game state."""

        class InspectingStep:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                if ctx.game_state.combat.is_active:
                    return StepResult.continue_with(ctx.with_updates(context_text="In combat"))
                return StepResult.continue_with(ctx.with_updates(context_text="Not in combat"))

        step = InspectingStep()

        # Test with combat inactive
        result = await step.run(self.ctx)
        assert result.context.context_text == "Not in combat"

        # Test with combat active
        self.game_state.combat.is_active = True
        result = await step.run(self.ctx)
        assert result.context.context_text == "In combat"

    @pytest.mark.asyncio
    async def test_step_protocol_with_dependencies(self) -> None:
        """Test step with injected dependencies."""

        class DependencyStep:
            def __init__(self, prefix: str):
                self.prefix = prefix

            async def run(self, ctx: OrchestrationContext) -> StepResult:
                updated = ctx.with_updates(context_text=f"{self.prefix}: {ctx.user_message}")
                return StepResult.continue_with(updated)

        step = DependencyStep(prefix="PROCESSED")
        result = await step.run(self.ctx)

        assert result.context.context_text == "PROCESSED: Test"

    @pytest.mark.asyncio
    async def test_step_protocol_with_events(self) -> None:
        """Test step that accumulates events."""

        class EventStep:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                from app.models.ai_response import StreamEvent, StreamEventType

                event = StreamEvent(type=StreamEventType.NARRATIVE_CHUNK, content="Step executed")
                updated = ctx.add_event(event)
                return StepResult.continue_with(updated)

        step = EventStep()
        result = await step.run(self.ctx)

        assert len(result.context.events) == 1
        assert result.context.events[0].content == "Step executed"

    @pytest.mark.asyncio
    async def test_multiple_steps_in_sequence(self) -> None:
        """Test running multiple steps in sequence."""

        class Step1:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                return StepResult.continue_with(ctx.with_updates(context_text="Step1"))

        class Step2:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                current = ctx.context_text
                return StepResult.continue_with(ctx.with_updates(context_text=f"{current} -> Step2"))

        class Step3:
            async def run(self, ctx: OrchestrationContext) -> StepResult:
                current = ctx.context_text
                return StepResult.continue_with(ctx.with_updates(context_text=f"{current} -> Step3"))

        # Run steps in sequence
        result1 = await Step1().run(self.ctx)
        assert result1.outcome == OrchestrationOutcome.CONTINUE

        result2 = await Step2().run(result1.context)
        assert result2.outcome == OrchestrationOutcome.CONTINUE

        result3 = await Step3().run(result2.context)
        assert result3.outcome == OrchestrationOutcome.CONTINUE
        assert result3.context.context_text == "Step1 -> Step2 -> Step3"
