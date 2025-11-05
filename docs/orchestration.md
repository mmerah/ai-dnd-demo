# Orchestration Architecture

The AI orchestration system uses a **composable pipeline architecture** consisting of 20 atomic steps that execute sequentially with conditional branching via guards.

## High-Level Flow

```
User Request
    ↓
AIService.generate_response()
    ↓ (creates OrchestrationContext)
    ↓
Pipeline.execute(context)
    ↓ (executes steps sequentially)
    ↓
┌───────────────┼───────────────────────┐
│               │                       │
▼               ▼                       ▼
NPC Dialogue    Agent Selection         Combat Management
(Steps 1-4)     (Steps 5-10)           (Steps 11-20)
```

## Detailed Pipeline Flow

```
1. DetectNpcDialogueTargets
   → Extract @npc_name mentions from user message
   ↓
   Guard: has_npc_targets?
   ├─ YES → 2. BeginDialogueSession (initialize dialogue state)
   │        3. ExecuteNpcDialogue (route to NPC agents)
   │        → Returns HALT (exits pipeline)
   │
   └─ NO → 4. EndDialogueSessionIfNeeded (cleanup if needed)
           ↓
           5. WrapAllyActionIfNeeded
              → If ally NPC turn, rewrite message for combat agent
           ↓
           6. SelectAgent
              → Read game_state.active_agent (NARRATIVE/COMBAT/NPC)
           ↓
           7. BuildAgentContext
              → Call context_service.build_context()
           ↓
           8. EnrichContextWithToolSuggestions
              → Call ToolSuggestorAgent, append suggestions to context
           ↓
           9. ExecuteAgent
              → Call narrative_agent or combat_agent.process()
           ↓
           10. ReloadState
               → Refresh game state after agent execution
           ↓
           Guard: combat state transitions?
           │
           ├─ combat_just_started?
           │  → 11. TransitionNarrativeToCombat (summarizer)
           │     12. SetCombatPhase(STARTING)
           │     13. GenerateInitialCombatPrompt
           │     14. BroadcastInitialPrompt
           │     ↓
           │     Guard: First turn type?
           │     ├─ Ally → GenerateAllySuggestion → HALT
           │     ├─ Player → ExecuteCombatAgent (prompts player)
           │     └─ Enemy → ExecuteCombatAgent → ReloadState → CombatLoop
           │
           ├─ combat_active?
           │  → CombatLoop (LoopStep, max 20 iterations):
           │     ├─ ReloadState
           │     ├─ Guard: no_enemies_remaining? → CombatAutoEnd
           │     ├─ Guard: is_ally_turn? → GenerateAllySuggestion → HALT
           │     └─ Guard: is_npc_or_monster_turn?
           │        → 15. GenerateCombatPrompt (with duplicate detection)
           │           16. BroadcastPrompt
           │           17. ExecuteCombatAgent
           │           → (loop continues until player turn or combat ends)
           │
           └─ combat_just_ended?
              → 18. SetCombatPhase(ENDED)
                 19. TransitionCombatToNarrative (summarizer + aftermath)
                 20. SetCombatPhase(INACTIVE)
```

## Core Components

### OrchestrationContext

Immutable dataclass carrying state through the pipeline:

```python
@dataclass(frozen=True)
class OrchestrationContext:
    user_message: str                      # Player's message
    game_state: GameState                  # Mutable game state (event-sourced)
    selected_agent_type: AgentType | None  # NARRATIVE/COMBAT/NPC
    context_text: str                      # Built context for agent
    flags: OrchestrationFlags              # combat_was_active, is_ally_turn, etc.
    events: list[StreamEvent]              # Accumulated stream events
```

### Step Protocol

All steps implement:

```python
class Step(Protocol):
    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Execute step logic, return CONTINUE/HALT/BRANCH."""
```

### Guards

Pure predicate functions for conditional execution:

```python
Guard = Callable[[OrchestrationContext], bool]

# Examples:
combat_just_started(ctx) -> bool
has_npc_targets(ctx) -> bool
is_current_turn_ally(ctx) -> bool
```

### Pipeline Construction

Declarative pipeline via `PipelineBuilder`:

```python
pipeline = (
    PipelineBuilder()
        .step(DetectNpcDialogueTargets(metadata_service))
        .when(has_npc_targets, steps=[
            BeginDialogueSession(),
            ExecuteNpcDialogue(...),
        ])
        .step(SelectAgent())
        .step(BuildAgentContext(context_service))
        # ... more steps
        .build()
)
```

## Reading and Extending the Pipeline

### Viewing the Current Pipeline

See `app/services/ai/orchestration/default_pipeline.py` (lines 115-253) for the canonical pipeline definition.

### Common Patterns

**1. Conditional Step Group**
```python
.when(guard_predicate, steps=[
    StepA(),
    StepB(),
])
```

**2. Conditional Loop**
```python
.when(should_loop, steps=[
    LoopStep(
        guard=continue_condition,
        steps=[...],
        max_iterations=20
    )
])
```

**3. Nested Conditionals**
```python
.when(outer_guard, steps=[
    StepA(),
    ConditionalStep(
        guard=inner_guard,
        steps=[StepB()]
    ),
])
```

### Adding a New Step

1. **Create step class** implementing `Step` protocol:
```python
# app/services/ai/orchestration/steps/my_step.py
class MyStep:
    async def run(self, ctx: OrchestrationContext) -> StepResult:
        # Your logic here
        updated_ctx = ctx.with_updates(...)
        return StepResult.continue_with(updated_ctx)
```

2. **Add to pipeline**:
```python
# app/services/ai/orchestration/default_pipeline.py
.step(MyStep(...))
```

3. **Write tests**:
```python
# tests/unit/services/ai/orchestration/steps/test_my_step.py
@pytest.mark.asyncio
async def test_my_step():
    ctx = OrchestrationContext(...)
    step = MyStep()
    result = await step.run(ctx)
    assert result.outcome == OrchestrationOutcome.CONTINUE
```

### Modifying Pipeline Flow

To change the execution order or add conditional logic, edit `default_pipeline.py`:

```python
# Example: Add validation before agent execution
.step(SelectAgent())
.step(BuildAgentContext(context_service))
.step(ValidateContext())  # NEW
.step(ExecuteAgent(...))
```

## Step Outcomes

- **CONTINUE**: Proceed to next step
- **HALT**: Stop pipeline immediately (e.g., NPC dialogue exits early)
- **BRANCH**: Reserved for future use

Guards determine whether conditional steps execute. Loop guards control iteration.

---

**See also**:
- Source: `app/services/ai/orchestration/`
- Tests: `tests/unit/services/ai/orchestration/`
