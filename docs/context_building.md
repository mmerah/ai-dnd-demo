# Context Building System

The context building system uses a **declarative composition pattern** to configure what information each AI agent receives.

## Architecture

```
ContextService
    ↓ initializes
BuilderRegistry (all builders) + Compositions (per agent type)
    ↓ agent requests context
ContextComposition.build(game_state) executes builders in order
    ↓ returns
Context string for agent
```

## Core Components

### Builders

Single-responsibility classes that extract specific context:

- **ContextBuilder**: Operates on game state (scenario, combat, quests, etc.)
- **EntityContextBuilder**: Operates on entities (spells, inventory, roleplay info)

Located in `app/services/ai/context/builders/`

### BuilderRegistry

Type-safe, immutable container holding all builder instances. Each builder is initialized once and reused.

### ContextComposition

Fluent API for declaring which builders to use:

```python
composition = (
    ContextComposition()
        .add(game_state_builder)              # Add game-state builder
        .add_for_entities(                    # Add entity builder with selector
            entity_builder,
            lambda gs: [gs.character]         # Selector function
        )
)
```

**Methods**:
- `.add(builder)` - Add game-state builder
- `.add_for_entity(builder, entity)` - Add builder for single entity
- `.add_for_entities(builder, selector)` - Add builder for multiple entities

### ContextService

Coordinator service that:
1. Creates `BuilderRegistry` with all builders
2. Defines `ContextComposition` for each agent type
3. Executes compositions to build context strings

## Configuration

Agent context configurations are in `app/services/ai/context/context_service.py`:

```python
def _create_compositions(self) -> dict[AgentType, ContextComposition]:
    b = self._builders
    return {
        AgentType.NARRATIVE: (
            ContextComposition()
                .add(b.scenario)
                .add(b.location)
                .add_for_entities(b.spells, lambda gs: [gs.character])
                # ... etc
        ),
        AgentType.COMBAT: ( ... ),
        AgentType.SUMMARIZER: ( ... ),
    }
```

## Common Tasks

### Modify Agent Context

1. Open `app/services/ai/context/context_service.py`
2. Edit `_create_compositions()` method
3. Add/remove/reorder builders in target agent's composition
4. Test: `pytest tests/unit/services/ai/context/`

### Add New Builder

1. Create `app/services/ai/context/builders/my_builder.py` implementing `ContextBuilder` or `EntityContextBuilder`
2. Add to `BuilderRegistry` in `_create_builders()`
3. Add to desired agent composition(s)
4. Write tests

### Use Entity Selector

Pass a lambda that extracts entities from game state:

```python
.add_for_entities(
    builder,
    lambda gs: [npc for npc_id in gs.party.member_ids
                if (npc := gs.get_npc_by_id(npc_id))]
)
```

## Design Principles

- **Declarative**: Compositions declare *what* to include, not *how*
- **Explicit**: Reading `_create_compositions()` shows exactly what each agent receives
- **Type-safe**: Full mypy compliance, no runtime config parsing
- **Testable**: Builders and compositions tested independently
- **Reusable**: Builders initialized once, composed differently per agent

---

**See also**:
- Source: `app/services/ai/context/`
- Tests: `tests/unit/services/ai/context/`
- Related: [docs/orchestration.md](orchestration.md)
