# Orchestrator Refactor Plan

## Scope & Goals
- Make orchestration configurable, extensible, and easy to test.
- Preserve existing behavior while improving clarity (SOLID, KISS, DRY).
- Enable “header code” pipeline configuration in Python (type-safe; no YAML for the pipeline).
- Support incremental rollout without breaking API contracts or frontend SSE flows.

Success criteria
- Functionally equivalent responses for narrative/combat and NPC dialogue.
- Unit tests for each orchestration step and key branches.
- Clear separation of concerns: selection, context, enrichment, execution, transitions, and loops.


## Decisions & Defaults (agreed)
- Pipeline toggles: keep minimal toggles; prefer a simple default pipeline assembled in code.
- Ally action handling: keep the current rewrite approach via a dedicated step (parity, KISS), with a future option to accept structured ally actions from API.
- Suggestions scope: enrich prompts for all agents (Narrative, Combat, NPC). For NPC agents, integrate suggestions during NPC prompt construction.
- Streaming: unchanged (SSE remains driven by event handlers; AIService continues as-is).
- Future agents: design pipeline/selection to easily add Level‑Up and Creator agents later.
- Reload frequency: allow multiple checkpoints where helpful (post-execution, post-combat loop, etc.).
- Config surface: pipeline is code-configured in `container.py`; no external YAML for orchestration.
- Test priorities: focus on combat (ally turns, initial prompt conditions, auto-prompting and end conditions).
- State machine: plan an explicit but lightweight FSM; avoid over‑engineering.


## Current Behavior Map (as‑is)

Entry points
- API action: `app/api/routers/game.py:138` → background task `process_ai_and_broadcast`
- Background task: `app/api/tasks.py:24` → `AIService.generate_response`
- AI service: `app/services/ai/ai_service.py:25` → `AgentOrchestrator.process`

Primary orchestrator flow
- `AgentOrchestrator.process` (`app/services/ai/orchestrator/orchestrator_service.py:31`)
  - NPC dialogue short-circuit (not in combat):
    - Extract targeted NPCs: `_extract_targeted_npcs` → `metadata_service.extract_targeted_npcs`.
    - If any, `_handle_npc_dialogue` (sets dialogue session, routes per targeted NPC via `IAgentLifecycleService.get_npc_agent`, agents self-build context/persona) → return early.
  - Combat special handling for allied NPC turn:
    - If combat active and current turn is ALLY NPC, rewrite player prompt to `[ALLY_ACTION] ...` instructing proper tool calls and `next_turn`.
  - Agent selection and context:
    - Determine `AgentType` via `agent_router.select` (returns `game_state.active_agent`).
    - Build agent context via `context_service.build_context(game_state, agent_type)`.
    - Pre-flight tool suggestions via `ToolSuggestorAgent` and append as a section to context.
  - Delegate to agent:
    - `agent.process(user_message, game_state, context, stream)` yields `StreamEvent`s.
  - State reload and transitions:
    - Reload `GameState` (`state_reload.reload → game_service.get_game`).
    - If combat just started: summarizer transition (Narrative→Combat), system prompt broadcast, initial combat prompt to `combat_agent` (skip if ally NPC turn), then `combat_loop.run`.
    - If combat is active: `combat_loop.run`.
    - If combat ended: summarizer transition (Combat→Narrative), then narrative aftermath prompt.

Combat loop (auto-continue)
- `app/services/ai/orchestrator/combat_loop.py`
  - Auto-end when enemies cleared: broadcasts system prompt and prompts `combat_agent` to end via tool.
  - Allied NPC turn: generate suggestion via NPC agent, broadcast suggestion (no auto-continue; UI decides).
  - Otherwise, auto-continue one iteration: generate prompt via `combat_service.generate_combat_prompt`, broadcast, run `combat_agent`.
  - Loop until break/guard or safety cap.

Observations
- Orchestrator concerns intermixed: detection, selection, context, enrichment, execution, transitions, looping, SSE messaging, state reloads.
- Early returns (NPC dialogue) and multi-branch post-processing complicate testing and reasoning.
- Implicit “state machine” across narrative/combat/dialogue is hardcoded in a single method.


## Pain Points
- Monolithic method with many dependencies; difficult to unit test in isolation.
- Hidden branching/early returns; non-obvious execution ordering and reload points.
- Hard-coded special cases (e.g., ally NPC message rewrite, suggestions enrichment inline).
- Context building + enrichment coupled to orchestrator (no composable pipeline stages).
- Combat transitions/loop logic wired inline rather than encapsulated.
- Limited configurability: cannot rearrange or toggle steps without editing core orchestrator.


## Target Architecture

Core concepts
- OrchestrationContext (dataclass): immutable-ish request/response container carried through the pipeline.
  - Fields: `user_message`, `game_state`, `incoming_agent_hint` (optional), `selected_agent_type`, `context_text`, `suggestions` (structured), `flags` (e.g., `is_ally_turn`, `npc_targets`, `combat_was_active`), `events` (captured stream events), `errors`.
- Step interface: `async def run(ctx: OrchestrationContext) -> OrchestrationOutcome`.
  - Outcome: continue with possibly updated context; or halt/branch with reason (e.g., `HALT_AFTER_NPC_DIALOGUE`).
  - Steps are small, pure-or-mostly-pure, easy to test. Side-effects go through ports (interfaces already exist).
- Pipeline: ordered list of Steps with simple guards (predicates over `ctx`).
  - Guards sample: `When(not combat_active)`, `When(combat_started)`, `When(combat_ended)`.
  - Branching via `When(..., steps=[...])` for transitions/loops.

Design details
- OrchestrationContext (frozen dataclass)
  - `@dataclass(frozen=True)` with a `with_updates(**kwargs)` helper that returns a new instance via `dataclasses.replace`.
  - Immutable inputs: `user_message`, `game_id`, optional `incoming_agent_hint`.
  - Mutable domain object note: `game_state` (Pydantic model) is inherently mutable; steps should cause state changes through the event bus/tools (event-sourced) and use `ReloadState` when fresh state is required.
  - Accumulators: `events: list[StreamEvent]`, `errors: list[str]` for observability.
- Step interface and result
  - `class OrchestrationOutcome(Enum): CONTINUE, HALT, BRANCH`.
  - `@dataclass(frozen=True) class StepResult: outcome, context, reason|None`.
  - `class Step(Protocol): async def run(self, ctx: OrchestrationContext) -> StepResult`.
- Guard predicates (type alias `Guard = Callable[[OrchestrationContext], bool]`)
  - `combat_just_started(ctx)`: `not ctx.flags.combat_was_active and ctx.game_state.combat.is_active`.
  - `combat_active(ctx)`: `ctx.game_state.combat.is_active`.
  - `combat_just_ended(ctx)`: `ctx.flags.combat_was_active and not ctx.game_state.combat.is_active`.
  - `has_npc_targets(ctx)`: `bool(ctx.flags.npc_targets)`.
- PipelineBuilder ergonomics
  - `PipelineBuilder.step(step)` appends an unconditional step.
  - `PipelineBuilder.when(guard, steps=[...])` appends a conditional group (`ConditionalStep`).
  - `PipelineBuilder.maybe(guard, step)` sugar for a single conditional step.
  - `PipelineBuilder.build()` returns an immutable `Pipeline(steps=...)`.

Key step categories
- Pre-routing
  - DetectNpcDialogueTargets
  - BeginDialogueSessionIfNeeded
  - WrapAllyActionIfNeeded (rewrites message for ALLY NPC turn)
- Selection & context
  - SelectAgent (strategy uses `agent_router`)
  - BuildAgentContext (`context_service`)
  - EnrichContextWithToolSuggestions (enabled for all agents; pluggable implementation)
- Execution
  - ExecuteAgent (delegates to selected agent, streams events)
  - ReloadState (unify reload points)
- Transitions & loops
  - TransitionNarrativeToCombat (summarizer + broadcasts)
  - TransitionCombatToNarrative (summarizer + aftermath prompt)
  - InitialCombatPrompt (system prompt broadcast + optional immediate combat action)
  - CombatAutoRun (encapsulates `combat_loop.run`)
- Dialogue
  - ExecuteNpcDialogue (routes to one or more NPC agents; signals `HALT` when done)

Configuration
- DefaultPipeline defined in code: a readable header-like declaration of steps and guards.
- PipelineBuilder for ergonomic composition and DI-friendly construction in `container.py`.
- Code-configured defaults; introduce feature flags only if necessary. Suggestions enrichment defaults to ON for all agents.

State machine (optional, later phase)
- States: Narrative, Combat, Dialogue.
- Events: `PLAYER_ACTION`, `COMBAT_STARTED`, `COMBAT_ENDED`, `ALLY_TURN`, `NPC_TARGETED`.
- Guards implement the same branching currently hardcoded; use a lightweight internal FSM rather than an external library.


## Proposed Default Pipeline (readable header code)

Pseudo-code sketch

```py
pipeline = (
  PipelineBuilder()
    .step(DetectNpcDialogueTargets())
    .when(lambda ctx: ctx.flags.npc_targets, steps=[
        BeginDialogueSession(),
        ExecuteNpcDialogue(),
        Halt()
    ])
    .step(WrapAllyActionIfNeeded())
    .step(SelectAgent(agent_router))
    .step(BuildAgentContext(context_service))
    .step(EnrichContextWithToolSuggestions(tool_suggestor_agent, for_agents="all"))
    .step(ExecuteAgent())
    .step(ReloadState(game_service))
    .when(combat_just_started, steps=[
        TransitionNarrativeToCombat(summarizer, event_bus),
        InitialCombatPrompt(combat_service, context_service, combat_agent),
        CombatAutoRun(combat_service, combat_agent, context_service, event_bus, lifecycle)
    ])
    .when(combat_active, steps=[
        CombatAutoRun(...)
    ])
    .when(combat_just_ended, steps=[
        TransitionCombatToNarrative(summarizer, event_bus, context_service, narrative_agent)
    ])
    .build()
)
```

This preserves current logic but makes each concern a small, testable unit.


## Phased Refactor Plan

Phase 0 — Baseline and tests
- Record baseline coverage and behavior before changes (pytest + coverage for orchestrator tests).
- Add unit tests for: NPC dialogue path, ally NPC turn wrapping, tool suggestions integration, all current state reload checkpoints, combat loop edge cases (safety cap, empty enemies).
- Add integration tests around `AIService.generate_response` with stub agents/bus to capture golden outputs.

Phase 1 — Introduce OrchestrationContext and Step interface (no behavior change)
- Phase 1a: Add context dataclass (frozen), Step protocol + StepResult, and guard helpers. No pipeline execution.
- Phase 1b: Implement one minimal step (e.g., `SelectAgent`) and invoke it from the legacy code path.
- Phase 1c: Add tests proving parity with current selection logic.

Phase 2 — Extract Dialogue path
- Implement `DetectNpcDialogueTargets`, `BeginDialogueSession`, `ExecuteNpcDialogue`, `Halt`.
- Replace inline dialogue block with steps; unit-test with mocked `IAgentLifecycleService`.

Phase 3 — Context enrichment as plugin
- Implement `EnrichContextWithToolSuggestions` (default ON) for all agent types.
- Keep `ContextService` unchanged; the step appends suggestion text if present.
- NPC agents: NPC agents build their own context internally via `context_service.build_context_for_npc()` and receive empty context string in `ExecuteNpcDialogue`. Two options for suggestions integration:
  - **Option A (recommended)**: Pass suggestions as a separate parameter to NPC agents and let them append to their self-built context.
  - **Option B**: Pre-build suggestions text in `ExecuteNpcDialogue` step and pass via a context override mechanism.
  - Choose Option A for consistency with NPC agent autonomy; modify `ExecuteNpcDialogue` to generate suggestions per NPC and pass them explicitly.
- Add tests verifying enrichment formatting and that suggestions appear for Narrative/Combat/NPC paths.

Phase 4 — Combat transitions and loop extraction
- Implement `TransitionNarrativeToCombat`, `InitialCombatPrompt`, `CombatAutoRun`, `TransitionCombatToNarrative` steps.
- Move code from `orchestrator_service`/`combat_loop` into these step classes (keep `combat_loop.run` as delegate until parity is proven, then inline or wrap it).
- Add tests for:
  - Combat start with/without ally turn.
  - Auto-end path and suggestion broadcast path.
  - Safety cap behavior.

Phase 5 — PipelineBuilder and default pipeline wiring
- Implement `PipelineBuilder` with `step`, `when`, `maybe`, and `build` semantics.
- Create `DefaultPipeline` declaration close to orchestrator module.
- Update `Container` to build `AgentOrchestrator(pipeline=DefaultPipeline, …deps)`.
- Keep legacy path available as `process_legacy()` in orchestrator.
- Add a code-configured feature switch `use_pipeline_orchestrator` (default: False) in container to choose the path.
- Optionally run both paths in parallel in a validation mode and log differences (no double side-effects).

Phase 6 — Optional: lightweight FSM (post‑MVP)
- Add explicit state enum and event transitions for narrative/combat/dialogue.
- Refactor guards to read state transitions rather than recomputing booleans.
- Keep Pipeline API intact; the FSM feeds guards.

Phase 7 — Extensibility enablement for new agents
- Provide selection rules and stubs to route to future Level‑Up and Creator agents without orchestrator rewrites.
- Add basic tests for selection fallback and guard composition.
- Design pipeline to support agent-specific pre/post steps for validation and memory capture.

Phase 8 — Cleanup, docs, and hardening
- Remove obsolete helpers/`process_legacy()` once parity is validated.
- Add thorough docstrings and diagrams to `docs/`.
- Update `CLAUDE.md` with the new orchestration architecture and extension points.


## Testing Strategy
- Unit tests per step with fake/stub ports for: event bus, game service, context service, agents.
- Integration tests for `AIService.generate_response` exercising:
  - NPC dialogue only path.
  - Narrative only.
  - Combat start → initial prompt (skip when ally turn) → auto-run → end.
  - Ally NPC turn: suggestion broadcast (no auto-continue) and accepted suggestion flow.
  - Ensure ally wrapper step does not double-wrap and preserves original content.
- Property-style tests for idempotent steps (e.g., WrapAllyActionIfNeeded; ReloadState fallback). Consider Hypothesis-based tests for ReloadState idempotency.
- mypy strict on new modules; forbid `Any` in step contracts.

Coverage & commands (baseline suggestion)
- `coverage run -m pytest tests/unit/services/ai/orchestrator/`
- `coverage report --include="app/services/ai/orchestrator/*"`

Observability & metrics
- Structured logging per step with `step`, `game_id`, and `agent_type` context.
- Measure: time per step, steps executed per request, halt reasons, reload count per request.

## Extensibility: Future Agents (Level‑Up, Creator)
- Selection strategy exposes a registry keyed by AgentType and/or guard predicates.
- Pipeline allows injection of agent-specific pre/post steps (e.g., validation, memory capture).
- For Level‑Up: guard triggers on level-up events; steps handle selection and context for leveling logic; execution via dedicated agent/tools.
- For Creator: guard allows invocation at any time based on explicit user intent or scenario gaps; steps isolate content creation from core narrative flow.


## Risks & Mitigations
- Behavioral drift: Mitigate with golden tests in Phase 0 and incremental swaps.
- Over-abstraction: Keep steps small and pragmatic; postpone FSM to Phase 6.
- Streaming interactions: Steps should not assume streaming; continue to rely on event bus for SSE output.
- Context bloat ("god object"): Keep OrchestrationContext lean; only include data needed across multiple steps. Step-specific data remains internal to the step.


## Work Breakdown & Deliverables
- PR1: Foundation (Phase 1a–1c)
  - OrchestrationContext (frozen), Step protocol + StepResult, Guard helpers
  - Minimal `SelectAgent` step integrated with legacy path
  - Tests + baseline coverage
- PR2: NPC Dialogue Extraction (Phase 2)
  - DetectNpcDialogueTargets, BeginDialogueSession, ExecuteNpcDialogue, Halt
  - Parity tests for NPC flows
- PR3: Tool Suggestions as Plugin (Phase 3)
  - EnrichContextWithToolSuggestions for all agents; NPC prompt integration
  - Integration tests
- PR4: Combat Orchestration (Phase 4)
  - TransitionNarrativeToCombat, InitialCombatPrompt, CombatAutoRun, TransitionCombatToNarrative
  - Extensive combat tests (ally turn, auto-run, end)
- PR5: Pipeline Assembly (Phase 5)
  - PipelineBuilder + DefaultPipeline
  - Container wiring with `use_pipeline_orchestrator` switch
  - Optional parallel validation logging
- PR6: Extensibility (Phase 7)
  - Selection rules and stubs for Level‑Up, Creator agents
  - Agent-specific pre/post step support
  - Routing tests
- PR7: Cleanup & Docs (Phase 8)
  - Remove legacy code after parity
  - Update docs and CLAUDE.md


## Validation & Rollout
- Use the `use_pipeline_orchestrator` switch in container to enable the new pipeline.
- Optionally run parallel validation (no side effects) to compare legacy vs pipeline outcomes in logs.
- Remove the legacy path only after parity proven in tests and manual validation.
