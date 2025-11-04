"""Tests for Pipeline and PipelineBuilder."""

import pytest

from app.models.ai_response import StreamEvent, StreamEventType
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.pipeline import ConditionalStep, Pipeline, PipelineBuilder
from app.services.ai.orchestration.step import OrchestrationOutcome, Step, StepResult
from tests.factories import make_game_state


# Test helper steps
class AddEventStep:
    """Step that adds a test event to the context."""

    def __init__(self, event_content: str) -> None:
        self.event_content = event_content

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        event = StreamEvent(type=StreamEventType.THINKING, content=self.event_content)
        updated_ctx = ctx.add_event(event)
        return StepResult.continue_with(updated_ctx)


class HaltStep:
    """Step that halts pipeline execution."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        return StepResult.halt(ctx, "Test halt")


class ErrorStep:
    """Step that raises an error."""

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        raise ValueError("Test error")


class TestConditionalStep:
    """Tests for ConditionalStep."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_conditional_step_guard_passes(self) -> None:
        """Test conditional step executes when guard passes."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        inner_step = AddEventStep("Conditional executed")
        conditional = ConditionalStep(guard=guard, steps=[inner_step])

        result = await conditional.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 1
        assert result.context.events[0].content == "Conditional executed"

    @pytest.mark.asyncio
    async def test_conditional_step_guard_fails(self) -> None:
        """Test conditional step skips when guard fails."""

        def guard(ctx: OrchestrationContext) -> bool:
            return False

        inner_step = AddEventStep("Should not execute")
        conditional = ConditionalStep(guard=guard, steps=[inner_step])

        result = await conditional.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 0

    @pytest.mark.asyncio
    async def test_conditional_step_multiple_steps(self) -> None:
        """Test conditional step executes multiple inner steps."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        steps = [
            AddEventStep("Event 1"),
            AddEventStep("Event 2"),
            AddEventStep("Event 3"),
        ]
        conditional = ConditionalStep(guard=guard, steps=steps)

        result = await conditional.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.CONTINUE
        assert len(result.context.events) == 3
        assert result.context.events[0].content == "Event 1"
        assert result.context.events[1].content == "Event 2"
        assert result.context.events[2].content == "Event 3"

    @pytest.mark.asyncio
    async def test_conditional_step_halts_on_inner_halt(self) -> None:
        """Test conditional step propagates HALT outcome."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        steps: list[Step] = [
            AddEventStep("Event 1"),
            HaltStep(),
            AddEventStep("Should not execute"),
        ]
        conditional = ConditionalStep(guard=guard, steps=steps)

        result = await conditional.run(self.ctx)

        assert result.outcome == OrchestrationOutcome.HALT
        assert result.reason == "Test halt"
        assert len(result.context.events) == 1  # Only first step executed


class TestPipeline:
    """Tests for Pipeline."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_pipeline_executes_steps_in_order(self) -> None:
        """Test pipeline executes steps sequentially."""
        steps = [
            AddEventStep("Event 1"),
            AddEventStep("Event 2"),
            AddEventStep("Event 3"),
        ]
        pipeline = Pipeline(steps=steps)

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 3
        assert events[0].content == "Event 1"
        assert events[1].content == "Event 2"
        assert events[2].content == "Event 3"

    @pytest.mark.asyncio
    async def test_pipeline_halts_on_halt_outcome(self) -> None:
        """Test pipeline stops when step returns HALT."""
        steps: list[Step] = [
            AddEventStep("Event 1"),
            HaltStep(),
            AddEventStep("Should not execute"),
        ]
        pipeline = Pipeline(steps=steps)

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 1
        assert events[0].content == "Event 1"

    @pytest.mark.asyncio
    async def test_pipeline_with_conditional_steps(self) -> None:
        """Test pipeline with conditional steps."""

        def guard_true(ctx: OrchestrationContext) -> bool:
            return True

        def guard_false(ctx: OrchestrationContext) -> bool:
            return False

        steps: list[Step | ConditionalStep] = [
            AddEventStep("Unconditional 1"),
            ConditionalStep(guard=guard_true, steps=[AddEventStep("Conditional true")]),
            ConditionalStep(guard=guard_false, steps=[AddEventStep("Conditional false")]),
            AddEventStep("Unconditional 2"),
        ]
        pipeline = Pipeline(steps=steps)

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 3
        assert events[0].content == "Unconditional 1"
        assert events[1].content == "Conditional true"
        assert events[2].content == "Unconditional 2"

    @pytest.mark.asyncio
    async def test_pipeline_raises_on_step_error(self) -> None:
        """Test pipeline propagates exceptions from steps."""
        steps: list[Step] = [
            AddEventStep("Event 1"),
            ErrorStep(),
            AddEventStep("Should not execute"),
        ]
        pipeline = Pipeline(steps=steps)

        with pytest.raises(ValueError, match="Test error"):
            async for _ in pipeline.execute(self.ctx):
                pass


class TestPipelineBuilder:
    """Tests for PipelineBuilder."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_builder_step_method(self) -> None:
        """Test PipelineBuilder.step() adds unconditional steps."""
        pipeline = PipelineBuilder().step(AddEventStep("Event 1")).step(AddEventStep("Event 2")).build()

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 2
        assert events[0].content == "Event 1"
        assert events[1].content == "Event 2"

    @pytest.mark.asyncio
    async def test_builder_when_method(self) -> None:
        """Test PipelineBuilder.when() adds conditional groups."""

        def guard_true(ctx: OrchestrationContext) -> bool:
            return True

        def guard_false(ctx: OrchestrationContext) -> bool:
            return False

        pipeline = (
            PipelineBuilder()
            .step(AddEventStep("Before"))
            .when(guard_true, steps=[AddEventStep("True branch")])
            .when(guard_false, steps=[AddEventStep("False branch")])
            .step(AddEventStep("After"))
            .build()
        )

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 3
        assert events[0].content == "Before"
        assert events[1].content == "True branch"
        assert events[2].content == "After"

    @pytest.mark.asyncio
    async def test_builder_chaining(self) -> None:
        """Test PipelineBuilder methods can be chained."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        pipeline = (
            PipelineBuilder()
            .step(AddEventStep("Step 1"))
            .when(guard, steps=[AddEventStep("Conditional")])
            .step(AddEventStep("Step 2"))
            .build()
        )

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_builder_complex_nesting(self) -> None:
        """Test PipelineBuilder with complex conditional nesting."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        pipeline = (
            PipelineBuilder()
            .step(AddEventStep("Start"))
            .when(
                guard,
                steps=[
                    AddEventStep("Nested 1"),
                    AddEventStep("Nested 2"),
                ],
            )
            .step(AddEventStep("End"))
            .build()
        )

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 4
        assert events[0].content == "Start"
        assert events[1].content == "Nested 1"
        assert events[2].content == "Nested 2"
        assert events[3].content == "End"


class TestPipelineIntegration:
    """Integration tests for Pipeline behavior."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_pipeline_with_halt_in_conditional(self) -> None:
        """Test pipeline halts when conditional step returns HALT."""

        def guard(ctx: OrchestrationContext) -> bool:
            return True

        pipeline = (
            PipelineBuilder()
            .step(AddEventStep("Before"))
            .when(
                guard,
                steps=[
                    AddEventStep("Conditional 1"),
                    HaltStep(),
                    AddEventStep("Should not execute"),
                ],
            )
            .step(AddEventStep("After - should not execute"))
            .build()
        )

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 2
        assert events[0].content == "Before"
        assert events[1].content == "Conditional 1"

    @pytest.mark.asyncio
    async def test_pipeline_guard_can_read_context_changes(self) -> None:
        """Test guards can observe context changes from previous steps."""

        class SetFlagStep:
            """Step that sets a flag in context."""

            async def run(self, ctx: OrchestrationContext) -> StepResult:
                updated_flags = ctx.flags.with_updates(combat_was_active=True)
                updated_ctx = ctx.with_updates(flags=updated_flags)
                return StepResult.continue_with(updated_ctx)

        def combat_was_active_guard(ctx: OrchestrationContext) -> bool:
            return ctx.flags.combat_was_active

        pipeline = (
            PipelineBuilder()
            .step(AddEventStep("Before"))
            .step(SetFlagStep())
            .when(combat_was_active_guard, steps=[AddEventStep("Combat was active")])
            .build()
        )

        events = [event async for event in pipeline.execute(self.ctx)]

        assert len(events) == 2
        assert events[0].content == "Before"
        assert events[1].content == "Combat was active"
