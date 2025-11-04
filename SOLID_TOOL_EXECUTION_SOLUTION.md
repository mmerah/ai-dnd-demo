# SOLID-Compliant Tool Execution Guard Solution

## Problem with Previous Approach

Adding `execution_state: dict[str, int]` to `AgentDependencies` violates SOLID:

- ❌ **SRP Violation**: AgentDependencies mixes service injection with execution state
- ❌ **Poor Separation**: Dependencies shouldn't track mutable state
- ❌ **Unclear Responsibility**: Is it a service container or a state holder?

---

## SOLID Solution: Separate Context and Guard

### Principle: Separate Concerns

1. **`ToolExecutionContext`** - Holds mutable execution state (data holder)
2. **`ToolExecutionGuard`** - Validates tool execution rules (service)
3. **`AgentDependencies`** - Injects both as dependencies (DI container)

Each class has a single, clear responsibility.

---

## Implementation

### File 1: Create the Context (Data Holder)

**New File:** `app/services/common/tool_execution_context.py`

```python
"""Execution context for tracking tool calls within an agent execution."""

from dataclasses import dataclass, field


@dataclass
class ToolExecutionContext:
    """Tracks tool execution state for a single agent execution.

    Lifetime: One agent execution (created fresh for each agent.process() call).

    This is a simple data holder with no business logic - all validation
    logic lives in ToolExecutionGuard service.
    """

    # Track how many times each tool has been called in this execution
    tool_call_counts: dict[str, int] = field(default_factory=dict)

    def increment_call_count(self, tool_name: str) -> int:
        """Increment call count for a tool and return new count."""
        current_count = self.tool_call_counts.get(tool_name, 0)
        new_count = current_count + 1
        self.tool_call_counts[tool_name] = new_count
        return new_count

    def get_call_count(self, tool_name: str) -> int:
        """Get current call count for a tool."""
        return self.tool_call_counts.get(tool_name, 0)

    def reset(self) -> None:
        """Reset all counters (typically not needed - create new instance instead)."""
        self.tool_call_counts.clear()
```

---

### File 2: Create the Guard (Service)

**New File:** `app/services/common/tool_execution_guard.py`

```python
"""Service for validating tool execution rules."""

import logging
from typing import Protocol

from app.models.tool_results import ToolErrorResult

logger = logging.getLogger(__name__)


class IToolExecutionContext(Protocol):
    """Protocol for tool execution context."""

    def get_call_count(self, tool_name: str) -> int:
        """Get current call count for a tool."""
        ...

    def increment_call_count(self, tool_name: str) -> int:
        """Increment and return new count."""
        ...


class ToolExecutionGuard:
    """Service for validating tool execution rules.

    Encapsulates business rules about tool usage:
    - How many times a tool can be called per execution
    - Which tools are mutually exclusive
    - Tool call ordering constraints
    """

    # Tools that can only be called once per agent execution
    SINGLE_USE_TOOLS = frozenset(["next_turn", "end_combat"])

    def __init__(self) -> None:
        """Initialize the guard."""
        pass

    def validate_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> ToolErrorResult | None:
        """Validate if a tool call should be allowed.

        Args:
            tool_name: Name of the tool being called
            context: Execution context tracking call counts

        Returns:
            ToolErrorResult if validation fails, None if allowed
        """
        # Check single-use tools
        if tool_name in self.SINGLE_USE_TOOLS:
            current_count = context.get_call_count(tool_name)

            if current_count > 0:
                error_msg = (
                    f"BLOCKED: {tool_name} has already been called {current_count} time(s) "
                    f"in this agent response. You can only call {tool_name} ONCE per turn."
                )

                suggestion = self._get_suggestion_for_tool(tool_name)

                logger.error(f"[TOOL_GUARD] {error_msg}")

                return ToolErrorResult(
                    error=error_msg,
                    tool_name=tool_name,
                    suggestion=suggestion,
                )

        # All validations passed
        return None

    def _get_suggestion_for_tool(self, tool_name: str) -> str:
        """Get helpful suggestion for blocked tool."""
        suggestions = {
            "next_turn": (
                "Remove duplicate next_turn calls. Only call next_turn once after completing the turn. "
                "Multiple next_turn calls skip turns and break combat order."
            ),
            "end_combat": (
                "Remove duplicate end_combat calls. Only call end_combat once when all enemies are defeated."
            ),
        }
        return suggestions.get(
            tool_name,
            f"Remove duplicate {tool_name} calls. This tool can only be called once per turn.",
        )

    def record_tool_call(
        self,
        tool_name: str,
        context: IToolExecutionContext,
    ) -> None:
        """Record that a tool was called (increment counter).

        Call this AFTER validation passes and BEFORE executing the tool.
        """
        new_count = context.increment_call_count(tool_name)
        logger.debug(f"[TOOL_GUARD] {tool_name} call #{new_count} recorded in execution context")
```

---

### File 3: Update AgentDependencies (DI Container)

**File:** `app/agents/core/dependencies.py`

```python
"""Agent dependencies for tool context."""

from dataclasses import dataclass

from app.agents.core.types import AgentType
from app.interfaces.events import IEventBus
from app.interfaces.services.common import IActionService
from app.interfaces.services.data import IRepository
from app.interfaces.services.game import IConversationService, IEventManager, IMetadataService, ISaveManager
from app.interfaces.services.scenario import IScenarioService
from app.models.game_state import GameState
from app.models.item import ItemDefinition
from app.models.monster import MonsterSheet
from app.models.spell import SpellDefinition
from app.services.common.tool_execution_context import ToolExecutionContext
from app.services.common.tool_execution_guard import ToolExecutionGuard


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools (Dependency Injection container).

    This class follows the Dependency Injection pattern - it holds references
    to services and state that tools need, but does not implement business logic itself.

    Lifetime: One agent execution (recreated for each agent.process() call).
    """

    # ===== Core State =====
    game_state: GameState

    # ===== Event & Command Services =====
    event_bus: IEventBus
    action_service: IActionService

    # ===== Agent Metadata =====
    agent_type: AgentType

    # ===== Domain Services =====
    scenario_service: IScenarioService
    conversation_service: IConversationService
    event_manager: IEventManager
    metadata_service: IMetadataService
    save_manager: ISaveManager

    # ===== Data Repositories =====
    item_repository: IRepository[ItemDefinition]
    monster_repository: IRepository[MonsterSheet]
    spell_repository: IRepository[SpellDefinition]

    # ===== Tool Execution Tracking =====
    # Context: Holds mutable execution state (data)
    tool_execution_context: ToolExecutionContext
    # Guard: Validates tool execution rules (service)
    tool_execution_guard: ToolExecutionGuard
```

**Why this is better:**
- ✅ **SRP**: Each dependency has a clear purpose
- ✅ **Explicit**: `tool_execution_context` name makes it clear what it's for
- ✅ **Testable**: Can mock `ToolExecutionGuard` in tests
- ✅ **Extensible**: Easy to add more execution rules to the guard

---

### File 4: Update Tool Decorator

**File:** `app/tools/decorators.py` (line 49-133, modify wrapper)

```python
@wraps(func)
async def wrapper(ctx: RunContext[AgentDependencies], **kwargs: Any) -> BaseModel:
    game_state = ctx.deps.game_state
    tool_name = func.__name__
    agent_type = ctx.deps.agent_type
    original_kwargs: dict[str, JSONSerializable] = cast(dict[str, JSONSerializable], dict(kwargs))

    # === NEW: Validate tool call using guard service ===
    guard = ctx.deps.tool_execution_guard
    execution_ctx = ctx.deps.tool_execution_context

    validation_error = guard.validate_tool_call(tool_name, execution_ctx)
    if validation_error:
        # Validation failed - return error to agent
        return validation_error

    # Validation passed - record the call
    guard.record_tool_call(tool_name, execution_ctx)

    # === EXISTING CODE: Prepare command, execute, handle errors ===
    if prepare is not None:
        prepared = prepare(dict(original_kwargs))
        if isinstance(prepared, tuple):
            command_kwargs = prepared[0]
            broadcast_kwargs: dict[str, JSONSerializable] = prepared[1]
        else:
            command_kwargs = prepared
            broadcast_kwargs = original_kwargs
    else:
        command_kwargs = original_kwargs
        broadcast_kwargs = original_kwargs

    # Build command (use factory if provided)
    # ... rest of existing code unchanged ...
```

---

### File 5: Update Agent Initialization

**File:** `app/agents/combat/agent.py` (lines 121-134)

```python
# Before (old):
deps = AgentDependencies(
    game_state=game_state,
    event_bus=self.event_bus,
    agent_type=AgentType.COMBAT,
    scenario_service=self.scenario_service,
    item_repository=item_repo,
    monster_repository=monster_repo,
    spell_repository=spell_repo,
    conversation_service=self.conversation_service,
    event_manager=self.event_manager,
    metadata_service=self.metadata_service,
    save_manager=self.save_manager,
    action_service=self.action_service,
)

# After (new):
from app.services.common.tool_execution_context import ToolExecutionContext
from app.services.common.tool_execution_guard import ToolExecutionGuard

deps = AgentDependencies(
    game_state=game_state,
    event_bus=self.event_bus,
    agent_type=AgentType.COMBAT,
    scenario_service=self.scenario_service,
    item_repository=item_repo,
    monster_repository=monster_repo,
    spell_repository=spell_repo,
    conversation_service=self.conversation_service,
    event_manager=self.event_manager,
    metadata_service=self.metadata_service,
    save_manager=self.save_manager,
    action_service=self.action_service,
    tool_execution_context=ToolExecutionContext(),  # ← Fresh context per execution
    tool_execution_guard=ToolExecutionGuard(),      # ← Guard service (could be singleton)
)
```

**Note:** Do the same for `narrative/agent.py`, `npc/base.py`, and any other agents.

---

## SOLID Principles Satisfied

### 1. Single Responsibility Principle (SRP) ✅

Each class has ONE reason to change:

- **`ToolExecutionContext`**: Changes only if execution state data structure changes
- **`ToolExecutionGuard`**: Changes only if tool validation rules change
- **`AgentDependencies`**: Changes only if dependencies change

### 2. Open/Closed Principle (OCP) ✅

**Extensible without modification:**

Want to add a new rule like "tool X and Y are mutually exclusive"?
→ Add to `ToolExecutionGuard.validate_tool_call()` - no changes to context or dependencies

Want to track additional state like "tool call timestamps"?
→ Add field to `ToolExecutionContext` - no changes to guard or dependencies

### 3. Liskov Substitution Principle (LSP) ✅

`IToolExecutionContext` protocol allows substitution:
- Can swap `ToolExecutionContext` with a mock in tests
- Guard depends on protocol, not concrete class

### 4. Interface Segregation Principle (ISP) ✅

Guard only depends on `IToolExecutionContext` protocol with 2 methods:
- Doesn't need to know about reset(), clear(), or internal structure
- Tools only see what they need via the guard service

### 5. Dependency Inversion Principle (DIP) ✅

- **High-level module** (tool decorator) depends on **abstraction** (`ToolExecutionGuard` service)
- **Low-level module** (`ToolExecutionContext`) implements **protocol** (`IToolExecutionContext`)
- Both depend on abstractions, not concretions

---

## Benefits Over Dict Approach

| Aspect | `execution_state: dict[str, int]` | `ToolExecutionContext + Guard` |
|--------|----------------------------------|-------------------------------|
| **SRP** | ❌ Mixed responsibilities | ✅ Separated data/logic |
| **Type Safety** | ❌ `dict[str, int]` is generic | ✅ Explicit methods |
| **Testability** | ⚠️ Hard to mock dict behavior | ✅ Easy to mock guard |
| **Extensibility** | ❌ Add more dicts? More keys? | ✅ Add methods to guard |
| **Clarity** | ❌ `deps.execution_state["next_turn_count"]` | ✅ `guard.validate_tool_call()` |
| **Encapsulation** | ❌ Direct dict access | ✅ Controlled via service |
| **Documentation** | ⚠️ Magic keys in dict | ✅ Self-documenting methods |

---

## Alternative: Singleton Guard vs Per-Execution Guard

**Current approach**: Create new `ToolExecutionGuard()` per execution

**Alternative**: Make guard a singleton (created once, injected from container)

```python
# In container.py:
self.tool_execution_guard = ToolExecutionGuard()  # Singleton

# In agent:
deps = AgentDependencies(
    # ...
    tool_execution_context=ToolExecutionContext(),     # New per execution
    tool_execution_guard=self.container.tool_execution_guard,  # Shared singleton
)
```

**Why singleton is better:**
- ✅ Guard has NO state - pure service
- ✅ Saves memory (one instance)
- ✅ Easier to extend with injected config
- ✅ Can inject rule definitions from config/database

**Recommendation**: Use singleton guard, per-execution context

---

## File Summary

**New Files** (2):
1. `app/services/common/tool_execution_context.py` (~30 lines)
2. `app/services/common/tool_execution_guard.py` (~70 lines)

**Modified Files** (5):
1. `app/agents/core/dependencies.py` (add 2 fields)
2. `app/tools/decorators.py` (add 10 lines for validation)
3. `app/agents/combat/agent.py` (add 2 lines to deps creation)
4. `app/agents/narrative/agent.py` (add 2 lines to deps creation)
5. `app/agents/npc/base.py` (add 2 lines to deps creation)

**Total**: ~120 lines of new code, following SOLID principles

---

## Testing

```python
# Test guard service
def test_guard_blocks_duplicate_next_turn():
    guard = ToolExecutionGuard()
    context = ToolExecutionContext()

    # First call should pass
    error = guard.validate_tool_call("next_turn", context)
    assert error is None
    guard.record_tool_call("next_turn", context)

    # Second call should be blocked
    error = guard.validate_tool_call("next_turn", context)
    assert error is not None
    assert "BLOCKED" in error.error
    assert error.tool_name == "next_turn"

# Test context tracking
def test_context_tracks_multiple_tools():
    context = ToolExecutionContext()

    assert context.get_call_count("next_turn") == 0
    context.increment_call_count("next_turn")
    assert context.get_call_count("next_turn") == 1

    context.increment_call_count("update_hp")
    assert context.get_call_count("update_hp") == 1
    assert context.get_call_count("next_turn") == 1  # Unchanged
```

---

## Conclusion

This solution is **SOLID-compliant** and production-ready:

- ✅ Clear separation of concerns (data vs logic)
- ✅ Testable (easy to mock guard and context)
- ✅ Extensible (add rules without modifying dependencies)
- ✅ Type-safe (no magic dict keys)
- ✅ Self-documenting (clear method names)
- ✅ Follows existing codebase patterns (service injection via container)

**Recommended approach**: Singleton `ToolExecutionGuard` + per-execution `ToolExecutionContext`
