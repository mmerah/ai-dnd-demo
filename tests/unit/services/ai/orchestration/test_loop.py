"""Tests for LoopStep (Phase 5.5)."""

from unittest.mock import AsyncMock

import pytest

from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.loop import LoopStep
from app.services.ai.orchestration.step import OrchestrationOutcome, StepResult
from tests.factories import make_game_state


class MockStep:
    """Mock step for testing LoopStep behavior."""

    def __init__(self, outcome: OrchestrationOutcome = OrchestrationOutcome.CONTINUE) -> None:
        self.outcome = outcome
        self.call_count = 0
        self.run = AsyncMock(side_effect=self._run_impl)

    async def _run_impl(self, ctx: OrchestrationContext) -> StepResult:
        self.call_count += 1
        if self.outcome == OrchestrationOutcome.HALT:
            return StepResult.halt(ctx, f"Mock halt at iteration {self.call_count}")
        return StepResult.continue_with(ctx)


class TestLoopStep:
    """Tests for LoopStep conditional iteration."""

    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.ctx = OrchestrationContext(user_message="Test", game_state=self.game_state)

    @pytest.mark.asyncio
    async def test_loop_executes_while_guard_passes(self) -> None:
        """Test loop continues executing while guard returns True."""
        iteration_count = 0

        def counting_guard(ctx: OrchestrationContext) -> bool:
            nonlocal iteration_count
            iteration_count += 1
            return iteration_count <= 3

        mock_step = MockStep()
        loop = LoopStep(guard=counting_guard, steps=[mock_step], max_iterations=10)

        result = await loop.run(self.ctx)

        # Guard passes on iterations 1, 2, 3, fails on 4
        assert mock_step.call_count == 3
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_loop_stops_when_guard_fails(self) -> None:
        """Test loop stops when guard returns False."""
        call_count = 0

        def guard(ctx: OrchestrationContext) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count <= 2

        mock_step = MockStep()
        loop = LoopStep(guard=guard, steps=[mock_step], max_iterations=10)

        result = await loop.run(self.ctx)

        assert mock_step.call_count == 2
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_loop_stops_on_halt_outcome(self) -> None:
        """Test loop stops immediately when step returns HALT."""

        def always_true(ctx: OrchestrationContext) -> bool:
            return True

        mock_continue = MockStep(OrchestrationOutcome.CONTINUE)
        mock_halt = MockStep(OrchestrationOutcome.HALT)

        loop = LoopStep(guard=always_true, steps=[mock_continue, mock_halt], max_iterations=10)

        result = await loop.run(self.ctx)

        assert mock_continue.call_count == 1
        assert mock_halt.call_count == 1
        assert result.outcome == OrchestrationOutcome.HALT
        assert "Mock halt at iteration 1" in (result.reason or "")

    @pytest.mark.asyncio
    async def test_loop_respects_max_iterations(self) -> None:
        """Test loop terminates after max_iterations safety cap."""

        def always_true(ctx: OrchestrationContext) -> bool:
            return True

        mock_step = MockStep()

        loop = LoopStep(guard=always_true, steps=[mock_step], max_iterations=5)

        result = await loop.run(self.ctx)

        assert mock_step.call_count == 5
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_loop_executes_multiple_steps_per_iteration(self) -> None:
        """Test loop executes all steps in each iteration."""
        iteration_count = 0

        def guard(ctx: OrchestrationContext) -> bool:
            nonlocal iteration_count
            iteration_count += 1
            return iteration_count <= 2

        step1 = MockStep()
        step2 = MockStep()
        step3 = MockStep()

        loop = LoopStep(guard=guard, steps=[step1, step2, step3], max_iterations=10)

        result = await loop.run(self.ctx)

        # Each iteration executes all 3 steps, guard passes twice
        assert step1.call_count == 2
        assert step2.call_count == 2
        assert step3.call_count == 2
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_loop_guard_evaluated_before_each_iteration(self) -> None:
        """Test guard is evaluated before each iteration, not during."""
        evaluations: list[int] = []

        def tracking_guard(ctx: OrchestrationContext) -> bool:
            evaluations.append(len(evaluations))
            return len(evaluations) <= 3

        mock_step = MockStep()
        loop = LoopStep(guard=tracking_guard, steps=[mock_step], max_iterations=10)

        await loop.run(self.ctx)

        # Guard evaluated: before iter 1, before iter 2, before iter 3, before iter 4 (fails)
        assert evaluations == [0, 1, 2, 3]
        assert mock_step.call_count == 3

    @pytest.mark.asyncio
    async def test_loop_context_accumulates_across_iterations(self) -> None:
        """Test context updates accumulate across iterations."""

        class CountingStep:
            def __init__(self) -> None:
                self.call_count = 0

            async def run(self, ctx: OrchestrationContext) -> StepResult:
                self.call_count += 1
                # Add marker to context
                updated = ctx.add_events([f"event-{self.call_count}"])  # type: ignore[list-item]
                return StepResult.continue_with(updated)

        counting_step = CountingStep()

        def guard(ctx: OrchestrationContext) -> bool:
            return counting_step.call_count < 3

        loop = LoopStep(guard=guard, steps=[counting_step], max_iterations=10)

        result = await loop.run(self.ctx)

        # Events accumulate across iterations
        assert len(result.context.events) == 3
        assert result.context.events[0] == "event-1"  # type: ignore[comparison-overlap]
        assert result.context.events[1] == "event-2"  # type: ignore[comparison-overlap]
        assert result.context.events[2] == "event-3"  # type: ignore[comparison-overlap]

    @pytest.mark.asyncio
    async def test_loop_no_iterations_when_guard_fails_immediately(self) -> None:
        """Test loop doesn't execute when guard fails on first check."""

        def always_false(ctx: OrchestrationContext) -> bool:
            return False

        mock_step = MockStep()

        loop = LoopStep(guard=always_false, steps=[mock_step], max_iterations=10)

        result = await loop.run(self.ctx)

        assert mock_step.call_count == 0
        assert result.outcome == OrchestrationOutcome.CONTINUE

    @pytest.mark.asyncio
    async def test_loop_halt_in_middle_of_multi_step_iteration(self) -> None:
        """Test loop halts immediately when any step in iteration returns HALT."""

        def always_true(ctx: OrchestrationContext) -> bool:
            return True

        step1 = MockStep(OrchestrationOutcome.CONTINUE)
        step2 = MockStep(OrchestrationOutcome.HALT)
        step3 = MockStep(OrchestrationOutcome.CONTINUE)

        loop = LoopStep(guard=always_true, steps=[step1, step2, step3], max_iterations=10)

        result = await loop.run(self.ctx)

        assert step1.call_count == 1
        assert step2.call_count == 1
        assert step3.call_count == 0  # Never reached
        assert result.outcome == OrchestrationOutcome.HALT
