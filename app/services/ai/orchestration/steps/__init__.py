"""Orchestration pipeline steps."""

from app.services.ai.orchestration.steps.begin_dialogue_session import (
    BeginDialogueSession,
)
from app.services.ai.orchestration.steps.broadcast_initial_prompt import (
    BroadcastInitialPrompt,
)
from app.services.ai.orchestration.steps.broadcast_prompt import BroadcastPrompt
from app.services.ai.orchestration.steps.build_agent_context import BuildAgentContext
from app.services.ai.orchestration.steps.combat_auto_end import CombatAutoEnd
from app.services.ai.orchestration.steps.detect_npc_dialogue import (
    DetectNpcDialogueTargets,
)
from app.services.ai.orchestration.steps.end_dialogue_session import EndDialogueSessionIfNeeded
from app.services.ai.orchestration.steps.enrich_suggestions import (
    EnrichContextWithToolSuggestions,
)
from app.services.ai.orchestration.steps.execute_agent import ExecuteAgent
from app.services.ai.orchestration.steps.execute_combat_agent import ExecuteCombatAgent
from app.services.ai.orchestration.steps.execute_npc_dialogue import ExecuteNpcDialogue
from app.services.ai.orchestration.steps.generate_ally_suggestion import (
    GenerateAllySuggestion,
)
from app.services.ai.orchestration.steps.generate_combat_prompt import (
    GenerateCombatPrompt,
)
from app.services.ai.orchestration.steps.generate_initial_combat_prompt import (
    GenerateInitialCombatPrompt,
)
from app.services.ai.orchestration.steps.reload_state import ReloadState
from app.services.ai.orchestration.steps.select_agent import SelectAgent
from app.services.ai.orchestration.steps.set_combat_phase import SetCombatPhase
from app.services.ai.orchestration.steps.transition_combat_narrative import (
    TransitionCombatToNarrative,
)
from app.services.ai.orchestration.steps.transition_narrative_combat import (
    TransitionNarrativeToCombat,
)
from app.services.ai.orchestration.steps.wrap_ally_action import WrapAllyActionIfNeeded

__all__ = [
    "BeginDialogueSession",
    "BroadcastInitialPrompt",
    "BroadcastPrompt",
    "BuildAgentContext",
    "CombatAutoEnd",
    "DetectNpcDialogueTargets",
    "EndDialogueSessionIfNeeded",
    "EnrichContextWithToolSuggestions",
    "ExecuteAgent",
    "ExecuteCombatAgent",
    "ExecuteNpcDialogue",
    "GenerateAllySuggestion",
    "GenerateCombatPrompt",
    "GenerateInitialCombatPrompt",
    "ReloadState",
    "SelectAgent",
    "SetCombatPhase",
    "TransitionCombatToNarrative",
    "TransitionNarrativeToCombat",
    "WrapAllyActionIfNeeded",
]
