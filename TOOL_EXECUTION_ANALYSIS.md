# Tool Execution Flow Analysis

## Critical Finding: Batch Tracking Won't Work

After tracing through the complete tool execution flow, **the combat_handler batch tracking approach is flawed**. Here's why:

---

## How Tool Calls Actually Execute

### Flow Trace:

1. **Agent starts** (`combat/agent.py:103-134`):
   ```python
   deps = AgentDependencies(
       game_state=game_state,
       event_bus=self.event_bus,
       agent_type=AgentType.COMBAT,
       # ... other services
   )
   # This deps object is created ONCE and reused for ALL tools in this execution
   ```

2. **Agent streams response** - Pydantic-AI generates tool calls as part of the LLM response stream

3. **For each tool call in the stream**:
   ```
   Tool (e.g., next_turn)
   → @tool_handler decorator (decorators.py:49)
   → action_service.execute_command_as_action() (action_service.py:124)
   → event_bus.execute_command() (action_service.py:163)
   → event_bus._run_command() (event_bus.py:74-110)
       ├── Loads game_state from memory (line 79)
       ├── Finds handler (line 82)
       ├── Calls handler.handle(command, game_state) (line 92)
       ├── Saves game_state if mutated (line 102)
       └── Returns result
   → Tool returns result to agent
   ```

4. **Next tool call** starts immediately after previous completes (synchronous execution)

---

## Why Batch Tracking Fails

### Problem 1: Handler is Stateless Across Tool Calls

The **combat_handler** has NO visibility into:
- Whether this is the 1st, 2nd, or 3rd call to `next_turn`
- Whether these calls are from the same agent execution or different ones
- When an agent execution starts or ends

From `combat_handler.py`, each call to `handle()` is independent:

```python
async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
    # Fresh invocation - no memory of previous tool calls
    if isinstance(command, NextTurnCommand):
        game_state.combat.next_turn()  # Executes immediately
        # How do we know if we already called next_turn in this agent response?
```

### Problem 2: Multiple Agents Can Run Concurrently

If we add `self._turn_advanced_this_batch = False` to combat_handler:
- Combat_handler is a **singleton** (one instance)
- Multiple agent executions could run concurrently
- Agent A calls next_turn → sets flag to True
- Agent B calls next_turn → sees flag is True → BLOCKS INCORRECTLY

### Problem 3: When to Reset the Flag?

Even for a single agent:
```python
# When does this reset?
if isinstance(command, (StartCombatCommand, StartEncounterCombatCommand)):
    self._turn_advanced_this_batch = False
```

StartCombatCommand happens at combat START, not at each agent execution. So the flag would never reset during combat!

---

## Why Timestamp Approach Also Fails

The alternative suggested approach:
```python
if current_time - self._last_next_turn_time < 0.5:
    # Block
```

**Problems:**
1. **Arbitrary timeout**: What if legitimate tool calls happen quickly?
2. **Concurrent agents**: Agent A and Agent B could both call next_turn within 0.5s
3. **Slow execution**: If tool #2 takes 600ms to execute, tool #3 would be allowed even though it's the same batch

---

## The Correct Solution: Track in AgentDependencies

The key insight: **`AgentDependencies` is created ONCE per agent execution and passed to ALL tools**.

From `combat/agent.py:121-134`:
```python
deps = AgentDependencies(
    game_state=game_state,
    event_bus=self.event_bus,
    agent_type=AgentType.COMBAT,
    # ...
)

# This deps object persists across ALL tool calls in this execution!
# It's passed as ctx.deps to every tool via RunContext[AgentDependencies]
```

### Solution: Add Mutable Execution State

**Step 1:** Modify `AgentDependencies` to include execution state:

**File:** `app/agents/core/dependencies.py`

```python
from dataclasses import dataclass, field

@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    event_bus: IEventBus
    agent_type: AgentType
    scenario_service: IScenarioService
    item_repository: IRepository[ItemDefinition]
    monster_repository: IRepository[MonsterSheet]
    spell_repository: IRepository[SpellDefinition]
    conversation_service: IConversationService
    event_manager: IEventManager
    metadata_service: IMetadataService
    save_manager: ISaveManager
    action_service: IActionService

    # NEW: Mutable execution state that persists across tool calls
    execution_state: dict[str, int] = field(default_factory=dict)
    # Usage: execution_state["next_turn_count"] tracks calls per execution
```

**Step 2:** Check and increment in the tool decorator:

**File:** `app/tools/decorators.py` (line 49-133, modify wrapper)

```python
@wraps(func)
async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
    game_state = ctx.deps.game_state
    tool_name = func.__name__
    agent_type = ctx.deps.agent_type
    original_kwargs: dict[str, JSONSerializable] = cast(dict[str, JSONSerializable], dict(kwargs))

    # === NEW: Track next_turn calls per agent execution ===
    if tool_name == "next_turn":
        # Get current count (default 0 if not set)
        next_turn_count = ctx.deps.execution_state.get("next_turn_count", 0)

        if next_turn_count > 0:
            # Already called next_turn in this agent execution!
            error_msg = (
                f"BLOCKED: next_turn has already been called {next_turn_count} time(s) "
                f"in this agent response. You can only call next_turn ONCE per turn. "
                f"Multiple next_turn calls skip turns and break combat order."
            )
            logger.error(f"[COMBAT] {error_msg}")

            return ToolErrorResult(
                error=error_msg,
                tool_name=tool_name,
                suggestion="Remove duplicate next_turn calls. Only call next_turn once after completing the turn.",
            )

        # Increment count BEFORE executing (so even if it fails, we've recorded the attempt)
        ctx.deps.execution_state["next_turn_count"] = next_turn_count + 1
        logger.info(f"[COMBAT] next_turn call #{ctx.deps.execution_state['next_turn_count']} in this execution")

    # === EXISTING CODE: Prepare command, execute, handle errors ===
    if prepare is not None:
        prepared = prepare(dict(original_kwargs))
        # ... rest of existing code ...
```

**Step 3:** No changes needed in combat_handler! The tool decorator blocks before the command even reaches the handler.

---

## Why This Works

1. **`AgentDependencies` lifetime = agent execution**
   - Created at start of `agent.process()`
   - Passed to ALL tool calls via `RunContext[AgentDependencies]`
   - Dies when agent.process() completes

2. **`execution_state` is a mutable dict**
   - Dataclasses without `frozen=True` are mutable
   - `dict` field is shared across all tool calls in this execution
   - Each new agent execution gets a fresh `execution_state` dict

3. **Blocking happens at tool level, not handler level**
   - Tool decorator checks BEFORE calling `action_service.execute_command_as_action()`
   - Returns `ToolErrorResult` to agent
   - Command never reaches combat_handler
   - Agent receives error message and (hopefully) learns not to do this

4. **No concurrency issues**
   - Each agent execution has its own `AgentDependencies` instance
   - Different agents can't interfere with each other's execution_state

5. **Automatic reset**
   - New agent execution → new `AgentDependencies` → new `execution_state` dict
   - No manual reset logic needed

---

## Implementation

### File Changes:

1. **`app/agents/core/dependencies.py`** (1 line added):
   ```python
   execution_state: dict[str, int] = field(default_factory=dict)
   ```

2. **`app/tools/decorators.py`** (~20 lines added):
   - Check `tool_name == "next_turn"`
   - Check `execution_state["next_turn_count"]`
   - If > 0, return `ToolErrorResult`
   - Otherwise, increment counter and continue

3. **`app/events/handlers/combat_handler.py`**: NO CHANGES NEEDED

---

## Testing

```python
# Test: Agent calls next_turn twice in one response
# Setup: Mock agent that generates:
#   Tool 1: update_hp(entity_id="goblin-1", damage=8)
#   Tool 2: next_turn()
#   Tool 3: next_turn()  # Should be blocked
# Expected:
#   - Tool 1 succeeds
#   - Tool 2 succeeds, advances turn
#   - Tool 3 blocked with ToolErrorResult
#   - Agent receives error message
#   - Turn only advanced once
```

---

## Alternative: Use Python contextvars (More Complex)

If we don't want to modify `AgentDependencies`, we could use Python's `contextvars`:

```python
from contextvars import ContextVar

_next_turn_count: ContextVar[int] = ContextVar('next_turn_count', default=0)

# At start of agent.process():
token = _next_turn_count.set(0)

# In tool decorator:
count = _next_turn_count.get()
if tool_name == "next_turn" and count > 0:
    # Block
_next_turn_count.set(count + 1)

# At end of agent.process():
_next_turn_count.reset(token)
```

**Pros:**
- No changes to AgentDependencies

**Cons:**
- More complex (contextvars are tricky)
- Requires careful cleanup in finally blocks
- Less explicit than execution_state dict

**Recommendation:** Use the `execution_state` dict approach - it's simpler, more explicit, and safer.

---

## Conclusion

The batch tracking in `combat_handler` won't work because:
- Handler is stateless across tool calls
- No visibility into agent execution boundaries
- Concurrency issues with singleton handler

The correct solution is to track state in `AgentDependencies.execution_state`, which:
- ✅ Persists across all tool calls in one agent execution
- ✅ Automatically resets for each new execution
- ✅ No concurrency issues (each agent has its own instance)
- ✅ Blocks at tool level before reaching handler
- ✅ Simple to implement (1 field + 20 lines)
