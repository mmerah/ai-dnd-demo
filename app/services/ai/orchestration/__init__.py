"""Orchestration package for composable pipeline architecture."""

from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.default_pipeline import create_default_pipeline
from app.services.ai.orchestration.guards import (
    Guard,
    combat_just_ended,
    combat_just_started,
    combat_loop_should_continue,
    has_npc_targets,
    is_current_turn_npc_or_monster,
    no_enemies_remaining,
)
from app.services.ai.orchestration.loop import LoopStep
from app.services.ai.orchestration.pipeline import ConditionalStep, Pipeline, PipelineBuilder
from app.services.ai.orchestration.step import OrchestrationOutcome, Step, StepResult

__all__ = [
    "OrchestrationContext",
    "OrchestrationFlags",
    "OrchestrationOutcome",
    "Step",
    "StepResult",
    "Guard",
    "combat_just_ended",
    "combat_just_started",
    "combat_loop_should_continue",
    "has_npc_targets",
    "is_current_turn_npc_or_monster",
    "no_enemies_remaining",
    "LoopStep",
    "Pipeline",
    "PipelineBuilder",
    "ConditionalStep",
    "create_default_pipeline",
]
