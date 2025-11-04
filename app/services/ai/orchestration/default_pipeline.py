"""Default orchestration pipeline factory.

This module provides the canonical pipeline configuration that replicates
the legacy orchestrator behavior. The pipeline is assembled in code using
PipelineBuilder for type safety and clarity.

Pipeline flow (see PLAN.md lines 143-171):
1. Detect NPC dialogue targets
2. If NPCs targeted → Begin dialogue session → Execute NPCs → HALT
3. Wrap ally action if needed
4. Select agent
5. Build agent context
6. Enrich with tool suggestions
7. Execute agent
8. Reload state
9. If combat just started → Transition → Initial prompt → Auto-run
10. If combat active → Auto-run
11. If combat just ended → Transition to narrative
"""

import logging

from app.agents.core.base import BaseAgent
from app.agents.tool_suggestor.agent import ToolSuggestorAgent
from app.interfaces.agents.summarizer import ISummarizerAgent
from app.interfaces.events import IEventBus
from app.interfaces.services.ai import IAgentLifecycleService, IContextService
from app.interfaces.services.game import (
    ICombatService,
    IConversationService,
    IEventManager,
    IGameService,
    IMetadataService,
)
from app.models.combat import CombatPhase
from app.services.ai.orchestration.guards import (
    combat_just_ended,
    combat_just_started,
    combat_loop_should_continue,
    has_npc_targets,
    is_current_turn_ally,
    is_current_turn_npc_or_monster,
    is_player_turn,
    no_enemies_remaining,
)
from app.services.ai.orchestration.loop import LoopStep
from app.services.ai.orchestration.pipeline import ConditionalStep, Pipeline, PipelineBuilder
from app.services.ai.orchestration.steps import (
    BeginDialogueSession,
    BroadcastInitialPrompt,
    BroadcastPrompt,
    BuildAgentContext,
    CombatAutoEnd,
    DetectNpcDialogueTargets,
    EndDialogueSessionIfNeeded,
    EnrichContextWithToolSuggestions,
    ExecuteAgent,
    ExecuteCombatAgent,
    ExecuteNpcDialogue,
    GenerateAllySuggestion,
    GenerateCombatPrompt,
    GenerateInitialCombatPrompt,
    ReloadState,
    SelectAgent,
    SetCombatPhase,
    TransitionCombatToNarrative,
    TransitionNarrativeToCombat,
    WrapAllyActionIfNeeded,
)

logger = logging.getLogger(__name__)


def create_default_pipeline(
    # Agent dependencies
    narrative_agent: BaseAgent,
    combat_agent: BaseAgent,
    summarizer_agent: ISummarizerAgent,
    tool_suggestor_agent: ToolSuggestorAgent,
    # Service dependencies
    context_service: IContextService,
    combat_service: ICombatService,
    game_service: IGameService,
    metadata_service: IMetadataService,
    conversation_service: IConversationService,
    agent_lifecycle_service: IAgentLifecycleService,
    event_manager: IEventManager,
    event_bus: IEventBus,
) -> Pipeline:
    """Create the default orchestration pipeline with explicit combat flow.

    This pipeline implements Phase 5.6 refactor with atomic combat steps
    and explicit turn-type handling. All dependencies are injected to
    support testing and flexibility.

    Args:
        narrative_agent: Agent for story progression
        combat_agent: Agent for tactical combat
        summarizer_agent: Agent for context transitions
        tool_suggestor_agent: Agent for tool suggestion generation
        context_service: Service for building agent context
        combat_service: Service for combat state management
        game_service: Service for game state persistence
        metadata_service: Service for extracting metadata from messages
        conversation_service: Service for recording conversation messages
        agent_lifecycle_service: Service for managing NPC agent lifecycle
        event_manager: Service for recording game events
        event_bus: Event bus for broadcasting system messages

    Returns:
        Configured Pipeline ready for execution
    """
    logger.info("Creating default orchestration pipeline")

    pipeline = (
        PipelineBuilder()
        # ===== NPC Dialogue Path (early exit) =====
        # TODO(MVP2): NPC agents do not receive tool suggestions because they exit early here
        # and build their own context internally (persona, memory, dialogue history).
        # Unlike Narrative/Combat agents which receive external context + suggestions,
        # NPCs are dialogue-focused with minimal tools (7 vs 15+) and self-construct context.
        # If tool suggestions become valuable for NPCs, consider generating suggestions
        # before this branch and passing them to ExecuteNpcDialogue to append to NPC context. Maybe
        # the asymmetry compared to the other agents could be removed to make NPC agents more
        # "ready" to be extended with context in the same way that narrative/combat agents are.
        .step(DetectNpcDialogueTargets(metadata_service))
        .when(
            has_npc_targets,
            steps=[
                BeginDialogueSession(),
                ExecuteNpcDialogue(agent_lifecycle_service, conversation_service),
                # ExecuteNpcDialogue returns HALT outcome to stop pipeline
            ],
        )
        # ===== End Dialogue Session (if no NPC targets and session is active) =====
        .step(EndDialogueSessionIfNeeded())
        # ===== Ally Turn Handling =====
        .step(WrapAllyActionIfNeeded())
        # ===== Agent Selection & Context =====
        .step(SelectAgent())
        .step(BuildAgentContext(context_service))
        .step(EnrichContextWithToolSuggestions(tool_suggestor_agent))
        # ===== Agent Execution =====
        .step(ExecuteAgent(narrative_agent, combat_agent))
        .step(ReloadState(game_service))
        # ===== Combat Start: Explicit Turn-Type Handling (Phase 5.6) =====
        .when(
            combat_just_started,
            steps=[
                TransitionNarrativeToCombat(summarizer_agent, event_bus),
                SetCombatPhase(CombatPhase.STARTING),
                GenerateInitialCombatPrompt(combat_service),
                BroadcastInitialPrompt(event_bus),
                # Handle first turn explicitly by type
                ConditionalStep(
                    guard=is_current_turn_ally,
                    steps=[
                        SetCombatPhase(CombatPhase.ACTIVE),
                        GenerateAllySuggestion(agent_lifecycle_service, event_bus),
                        # Returns HALT - exits pipeline, waits for user acceptance
                    ],
                ),
                ConditionalStep(
                    guard=is_player_turn,
                    steps=[
                        SetCombatPhase(CombatPhase.ACTIVE),
                        ExecuteCombatAgent(combat_agent, context_service),
                        # Agent asks player for action, pipeline ends, waits for input
                    ],
                ),
                ConditionalStep(
                    guard=is_current_turn_npc_or_monster,
                    steps=[
                        ExecuteCombatAgent(combat_agent, context_service),
                        ReloadState(game_service),
                        SetCombatPhase(CombatPhase.ACTIVE),
                        # After initial enemy turn, continue auto-executing subsequent enemy turns
                        LoopStep(
                            guard=combat_loop_should_continue,
                            steps=[
                                ReloadState(game_service),
                                ConditionalStep(
                                    guard=no_enemies_remaining,
                                    steps=[CombatAutoEnd(combat_agent, context_service, event_bus, game_service)],
                                ),
                                ConditionalStep(
                                    guard=is_current_turn_ally,
                                    steps=[GenerateAllySuggestion(agent_lifecycle_service, event_bus)],
                                ),
                                ConditionalStep(
                                    guard=is_current_turn_npc_or_monster,
                                    steps=[
                                        GenerateCombatPrompt(combat_service),
                                        BroadcastPrompt(event_bus),
                                        ExecuteCombatAgent(combat_agent, context_service),
                                    ],
                                ),
                            ],
                            max_iterations=20,
                        ),
                    ],
                ),
            ],
        )
        # ===== Check for Auto-End (after any combat action) =====
        .when(
            no_enemies_remaining,
            steps=[CombatAutoEnd(combat_agent, context_service, event_bus, game_service)],
        )
        # ===== Combat Continuation (after player/ally actions) =====
        .when(
            combat_loop_should_continue,
            steps=[
                LoopStep(
                    guard=combat_loop_should_continue,
                    steps=[
                        ReloadState(game_service),
                        ConditionalStep(
                            guard=no_enemies_remaining,
                            steps=[CombatAutoEnd(combat_agent, context_service, event_bus, game_service)],
                        ),
                        ConditionalStep(
                            guard=is_current_turn_ally,
                            steps=[GenerateAllySuggestion(agent_lifecycle_service, event_bus)],
                        ),
                        ConditionalStep(
                            guard=is_current_turn_npc_or_monster,
                            steps=[
                                GenerateCombatPrompt(combat_service),
                                BroadcastPrompt(event_bus),
                                ExecuteCombatAgent(combat_agent, context_service),
                            ],
                        ),
                    ],
                    max_iterations=20,
                ),
            ],
        )
        # ===== Combat End Transition =====
        .when(
            combat_just_ended,
            steps=[
                SetCombatPhase(CombatPhase.ENDED),
                TransitionCombatToNarrative(
                    summarizer_agent,
                    event_bus,
                    context_service,
                    narrative_agent,
                ),
                SetCombatPhase(CombatPhase.INACTIVE),
            ],
        )
        .build()
    )

    logger.info("Default pipeline created with %d top-level steps", len(pipeline._steps))
    return pipeline
