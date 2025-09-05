# CLAUDE-REVIEW.md - Critical Issues Analysis for MVP1

## Executive Summary

This document provides a comprehensive analysis of the 4 critical issues identified in IDEAS.md for MVP1. Each issue has been thoroughly investigated through code analysis, execution path tracing, and architectural review.

## Issue 1: Game State Model Review - Scenarios, Acts, Quests, Locations, NPCs

### Current State Analysis

#### Model Architecture Observations

1. **Data/Model Mismatch (npc_ids)**
   - Location JSON files contain `npc_ids` (e.g., `locations/tavern.json`)
   - `ScenarioLocation` does not define `npc_ids`
   - NPC presence is already tracked via `NPCInstance.current_location_id`
   - Resolution direction: remove `npc_ids` from data rather than adding it to the model

2. **Duplicate Data Structures**
   ```python
   # In location JSON files:
   "npc_ids": ["barkeep-tom"]
   
   # In ScenarioLocation model:
   notable_monsters: list[ScenarioMonster]  # Different naming
   monster_ids: list[str]                   # No NPC equivalent
   ```

3. **Optional/Required Fields**
   - `scenario.py:142`: `id` currently has `default="default"`. Making it required is acceptable but not critical for MVP1.
   - `scenario.py:56`: `descriptions` are optional by design with clear fallback to `description`; keep optional.
   - `scenario_instance.py:28-29`: Uses a sentinel `"unknown-location"` instead of `None` for type safety; this is intentional and should be kept.

4. **NPC Population Logic** (`game_service.py:598-614`)
   - All NPCs loaded at game start regardless of location
   - **User Feedback**: This is acceptable for MVP1. Added NOTE comment for future enhancement.
   - No efficient query mechanism for "NPCs at location X" - still needs implementation
   - ChangeLocation currently does not validate connections/requirements

### Proposed Fixes

#### 1. Clean up location JSON files
**Action**: Remove any `npc_ids` references from location JSON files (NPCs track their own location).

#### 2. Remove Model Defaults Where Inappropriate
```python
class ScenarioSheet(BaseModel):
    id: str  # Consider removing default="default" (optional for MVP1)
    title: str
    # ... rest
```

#### 3. Implement NPC Location Queries in GameState [Still Valid]
```python
# app/models/game_state.py
def get_npcs_at_location(self, location_id: str) -> list[NPCInstance]:
    """Get all NPCs currently at the specified location."""
    return [npc for npc in self.npcs if npc.current_location_id == location_id]
```


#### 5. Location Change Validation (New)
Add connection/requirement validation before moving:
```python
# app/events/handlers/location_handler.py
# Before calling game_state.change_location(...),
# ensure a visible, traversable connection exists from current → target.
```

#### 6. Unknown Location Handling (Keep Sentinel)
Keep `"unknown-location"` sentinel for ephemeral/transition states to avoid persisting junk state and to keep types non-optional. See `GameState.get_location_state()` special-casing.

#### 7. Conditions Source of Truth (New)
Prefer updating conditions on entity runtime state (`NPCInstance.state.conditions`, `Monster.conditions`). Avoid duplicating mutable conditions on `CombatParticipant` or ensure strict synchronization if kept.

---

## Issue 2: Combat System Implementation

### Additional Context from User Feedback
- **Monster Storage**: Monsters are stored as raw `Monster` objects in `game_state.monsters`, not as instances like NPCs
- **Monster Location**: No location tracking for monsters - they're spawned on-demand during combat
- **Monster Instances**: Consider future enhancement where monsters could have `MonsterInstance` with location tracking similar to NPCs
- **CombatParticipant ID**: Uses `name` as identifier, which is why duplicate names get suffixed (e.g., "Goblin 2")

### Current State Analysis

#### What's Implemented ✅
- **Combat Models**: CombatState, CombatParticipant, initiative tracking
- **Combat Initialization**: start_combat, trigger_scenario_encounter tools
- **Supporting Systems**: Dice rolling, HP management, condition tracking
- **Frontend Integration**: Combat indicator, initiative display

#### What's Missing ❌
1. **Turn Management Tools**
   - No `next_turn` tool for AI
   - No `end_combat` tool
   - No turn order display tool

2. **Combat Action Tools**
   - No `make_attack` tool
   - No damage resolution flow
   - No action economy tracking (Action/Bonus/Movement)

3. **Combat Agent**
   - `factory.py:114-115`: Combat agent explicitly not implemented
   - No combat-specific system prompt

### Proposed Implementation [UPDATED]

#### 1. Add Turn Management Tools [CONFIRMED NEEDED]
**Architecture note**: Tools should be declared with `@tool_handler` and route to event-bus commands; handlers update `GameState` and broadcast.

**Note on CombatParticipant**: Currently uses `name` as identifier. This works because duplicate names get suffixed ("Goblin 2"). Consider unique IDs later for robustness.

```python
# app/tools/combat_tools.py

@tool_handler(NextTurnCommand)
async def advance_turn(ctx: RunContext[AgentDependencies]) -> BaseModel:
    """
    Advance to the next turn in combat.
    
    Examples:
    - "The goblin's turn is over, moving to the next combatant"
    - "End of round, starting new round"
    """
    game_service = ctx.deps.game_service
    game_state = ctx.deps.game_state
    
    if not game_state.combat:
        return ToolResult(message="No active combat")
    
    old_participant = game_state.combat.get_current_turn()
    game_state.combat.next_turn()
    new_participant = game_state.combat.get_current_turn()
    game_service.save_game(game_state)
    return ToolResult(message=f"Turn advanced: {old_participant and old_participant.name} → {new_participant and new_participant.name}")

@tool_handler(EndCombatCommand)
async def end_combat(ctx: RunContext[AgentDependencies]) -> BaseModel:
    """End the current combat encounter."""
    game_service = ctx.deps.game_service
    game_state = ctx.deps.game_state
    
    if not game_state.combat:
        return ToolResult(message="No active combat to end")
    
    game_state.end_combat()  # cleans up defeated monsters
    game_service.save_game(game_state)
    return ToolResult(message="Combat has ended")
```

#### 1a. Extend CombatState for Better Display
```python
# app/models/combat.py - Add method to CombatState

def get_turn_order_display(self) -> str:
    """Get formatted turn order for display."""
    if not self.participants:
        return "No participants in combat"
    
    current = self.get_current_turn()
    lines = [f"Round {self.round_number} - Turn Order:"]
    
    for i, p in enumerate(self.participants):
        if p.is_active:
            marker = "→ " if p == current else "  "
            status = f" [{', '.join(p.conditions)}]" if p.conditions else ""
            lines.append(f"{marker}{p.name} (Initiative: {p.initiative}){status}")
    
    return "\n".join(lines)
```

#### 1b. Conditions Duplication (New)
Either remove `conditions` from `CombatParticipant` and read from entity state in displays, or keep it as a view-only denormalized list but always synchronize via handlers to avoid drift.

#### 2. Add Combat Commands for Turn Management
**Note**: Tools route through event-bus commands/handlers for consistency.
```python
# app/events/commands/combat_commands.py

@dataclass(frozen=True)
class NextTurnCommand(Command):
    """Advance to next combat turn."""
    pass

@dataclass(frozen=True)
class EndCombatCommand(Command):
    """End current combat."""
    pass
```

---

## Issue 3: TODO Comments Resolution

### Priority 1: Critical TODOs

#### 1. ContextService Architecture (`app/services/ai/context_service.py:13`) [CONFIRMED]
**TODO**: "Could just deep-load GameState and Scenario no?"
**Solution**: Remove IScenarioService dependency, use embedded scenario from GameState
```python
# Before:
self.scenario_service = scenario_service
context = self.scenario_service.get_scenario_context_for_ai(...)

# After:
scenario = game_state.scenario_instance.sheet
location = scenario.get_location(game_state.scenario_instance.current_location_id)
```

#### 2. Duplicate Method (`app/services/game/game_service.py:561`) [CONFIRMED]
**TODO**: "Look unused. GameState has a method with exact same name"
**Solution**: Delete the duplicate `set_quest_flag` method in GameService

### Priority 2: Important TODOs

#### 3. Repository Bidirectional Lookups (`app/services/character/compute_service.py:286`)
**TODO**: "Need a way to get name from index for ALL repositories"
**Solution**: Add reverse lookup interface to all repositories
```python
class IRepository(Protocol):
    def get_name_from_index(self, index: int) -> str | None:
        """Get name from index, inverse of get_index_from_name."""
```

#### 4. NPC Movement (`app/events/handlers/location_handler.py:116`)
**TODO**: "Need a way/tool to move NPCInstance to another location"
**Solution**: Add NPC movement tool
```python
@agent.tool
async def move_npc_to_location(
    ctx: RunContext[AgentDependencies],
    npc_name: str,
    location_name: str
) -> str:
    """Move an NPC to a different location."""
```

#### 5. SSE Events Review (`app/models/sse_events.py:69-70`)
**TODO**: "Generally, those SSE events, are they useful?"
**Solution**: Audit frontend usage, remove if unused

### Priority 3: Nice-to-Have TODOs

#### 6. Equipment Slots (`app/services/game/game_service.py:417`)
**TODO**: "Future: move to a slot-based equipment system"
**Solution**: Defer to MVP2, current quantity system works

#### 7. Narrative Formatting (`app/models/scenario.py:193`)
**TODO**: "Don't make it too formatted"
**Solution**: Simplify formatting in `get_initial_narrative()`

#### 8. Random Encounters (`app/services/data/loaders/scenario_loader.py:88`)
**TODO**: "Load random encounters if needed"
**Solution**: Implement in MVP2 for variety

---

## Issue 4: ContextService Simplification

### Current Problems

1. **Unnecessary Dependencies**
   - Depends on IScenarioService just for 8-line method
   - Scenario data already in GameState

2. **Overcomplicated Architecture**
   - 341 lines with 10+ private methods
   - Complex dependency injection
   - Verbose context output

3. **Data Access Patterns**
   - Goes through service layers for data in GameState
   - Creates unnecessary coupling
   - Repositories remain useful for optional enrichment (items/spells)

### Proposed Simplification

#### Step 1: Remove IScenarioService Dependency
```python
# app/services/ai/context_service.py
class ContextService:
    def __init__(
        self,
        # Remove: scenario_service: IScenarioService,
        item_repository: IItemRepository | None = None,
        spell_repository: ISpellRepository | None = None,
    ):
        # Direct access to GameState data; keep repos optional for enrichment
```

#### Step 2: Simplify Context Building
```python
def build_context(self, game_state: GameState) -> str:
    """Build AI context directly from GameState."""
    
    scenario = game_state.scenario_instance.sheet
    location = scenario.get_location(game_state.scenario_instance.current_location_id)
    
    # Build streamlined context
    context_parts = [
        f"# Scenario: {scenario.title}",
        f"## Current Location: {location.name}",
        self._build_location_context(location, game_state),
        self._build_npc_context(game_state),
        self._build_quest_context(game_state),
        self._build_character_context(game_state),
    ]
    
    if game_state.combat:
        context_parts.append(self._build_combat_context(game_state))
    
    return "\n\n".join(filter(None, context_parts))
```

#### Step 3: Update Factory
```python
# app/agents/factory.py
context_service = ContextService(
    # Remove scenario_service parameter
    item_repository=self.item_repository,
    spell_repository=self.spell_repository,
)
```

---


---

## Risk Assessment

### High Risk Areas
1. **Combat Turn Tools**: Missing turn tools can limit playability during combat until added
2. **Location Validation**: Adding traversal validation may surface issues in scenario data

### Medium Risk Areas
1. **ContextService Refactor**: Affects AI decision-making
2. **Data Cleanup**: Removing unused fields from JSON requires small data updates

### Low Risk Areas
1. **TODO Cleanup**: Mostly code quality improvements
2. **Optional Field Changes**: Backward compatible

---

## Conclusion [UPDATED]

Based on user feedback, the revised priorities for MVP1 are:

### Immediate Actions Required:

1. **Game State Models**: 
   - Remove `npc_ids` from location JSON files (NPCs track their own location)
   - Implement NPC location queries in GameState
   - Add ChangeLocation traversal validation (use connections + requirements)
   - Consider future MonsterInstance for location-aware monsters

2. **Combat System**:
   - Add only `next_turn` and `end_combat` tools
   - Extend CombatState for turn order display
   - No combat agent or action tools needed - narrative agent handles everything
   - No action economy tracking for MVP1
   - Address conditions duplication (source of truth on entity state)

3. **TODO Comments**:
   - Delete duplicate `set_quest_flag` method
   - Simplify ContextService architecture
   - Other TODOs can be deferred

4. **ContextService**:
   - Remove IScenarioService dependency
   - Use embedded scenario from GameState directly

### Key Simplifications from Feedback:
- NPCs tracking their own location is cleaner than bidirectional references
- AI DM flexibility is better than automated combat mechanics
- Narrative agent suffices for MVP1 without specialized agents
- Loading all NPCs at start is acceptable for MVP1
- Keep `unknown-location` sentinel to avoid Optional fields and prevent persisting transitional state

---

## Issue 5: Entity Architecture and Combat Integration [NEW INVESTIGATION]

### Current State - Critical Architectural Inconsistency

#### Entity Storage Patterns (MAJOR INCONSISTENCY)
```
CharacterInstance → CharacterSheet + EntityState  (Template + Runtime state)
NPCInstance      → NPCSheet + EntityState        (Template + Runtime state)  
Monster          → Raw Monster object only        (Mixed template/runtime)
```

#### The Problems

1. **Monster Architecture Mismatch**
   - Monsters stored as raw `Monster` objects in `game_state.monsters`
   - No separation between template and runtime state
   - Monster model mixes static data (name, CR) with runtime (HP, conditions)
   - No location tracking for monsters (unlike NPCs)

2. **CombatParticipant Weakness** (`app/models/combat.py:6-14`)
   ```python
   class CombatParticipant(BaseModel):
       name: str              # Only identifier
       initiative: int | None
       is_player: bool
       is_active: bool
       conditions: list[str]  # Duplicated from entity state!
   ```
   - Uses name as ID (fragile, requires suffixing for duplicates)
   - No reference to actual entity (Character/NPC/Monster)
   - Conditions duplicated, not synced with entity state

3. **Tool Limitations** (`app/events/handlers/character_handler.py:46-69`)
   - `update_hp` only handles "player" and NPC names
   - **MONSTERS CANNOT BE DAMAGED THROUGH TOOLS**
   - Handler searches NPCs by name but ignores monsters entirely
   - No way to apply conditions to monsters

4. **Combat Flow Issues**
   - Combat spawns monsters into `game_state.monsters`
   - Monsters removed when dead after combat ends
   - No persistent monster instances between encounters
   - No way to have recurring monsters or track monster state

### Architecture Analysis

#### Why This Happened
- NPCs were designed with rich instance/template separation
- Monsters were added later as simpler entities
- Combat system built assuming name-based references
- Tools evolved organically without unified entity interface

#### Current Workarounds
- Monsters get name suffixes ("Goblin 2") for uniqueness
- AI must track monster HP narratively
- No tool support for monster damage/conditions

### Proposed Solution: Two-Phase Complete Fix

Assumptions
- No backward compatibility. We will fully transition data models, save format, and API types.

#### Phase 1: MonsterInstance Pattern (Fixes Architecture)
Repository and Data
- Keep `data/monsters.json` as-is. The mapping logic in `app/services/data/repositories/monster_repository.py` remains valid — only the model name/type changes.
- Rename model `Monster` → `MonsterSheet` and update repository imports/generics/returns accordingly so all repository methods return `MonsterSheet`.
  - `app/services/data/repositories/monster_repository.py:1` (imports)
  - `app/services/data/repositories/monster_repository.py:18` (`BaseRepository[Monster]` → `BaseRepository[MonsterSheet]`)
  - `app/services/data/repositories/monster_repository.py:99` (`_load_item` return type)
  - Other return annotations like `get_by_challenge_rating`, `get_by_type`.

Scenario References
- Update `ScenarioMonster.monster: Monster` → `MonsterSheet` (`app/models/scenario.py:10`, `app/models/scenario.py:139`).
- Update `ScenarioService.get_scenario_monster(...)` to return `MonsterSheet` (`app/services/scenario/scenario_service.py:116`, `app/services/scenario/scenario_service.py:131`).

Runtime State
- Add `MonsterInstance` (parallel to `NPCInstance`) with `sheet: MonsterSheet` and `state: EntityState`.
- Change `GameState.monsters` from `list[Monster]` to `list[MonsterInstance]` (`app/models/game_state.py:43`).

Save Format (full transition)
- Store monsters under `instances/monsters/{instance_id}.json` (consistent with NPCs), not in top-level `monsters/`.
- Replace `_save_monsters`/`_load_monsters` with `_save_monster_instances`/`_load_monster_instances`:
  - Replace logic at `app/services/game/save_manager.py:273` and `app/services/game/save_manager.py:361`.
  - Integrate with `_save_instances` directory (`app/services/game/save_manager.py:241`).

Handlers and Tools
- Spawn paths in `app/events/handlers/combat_handler.py:96` and `app/events/handlers/combat_handler.py:131` must instantiate `MonsterInstance` (assign `instance_id`, build `EntityState` from `MonsterSheet`).
- Extend `UpdateHP` and `UpdateCondition` to target monsters by name initially; Phase 2 will move to id-based resolution.
```python
# app/models/instances/monster_instance.py
class MonsterInstance(BaseModel):
    """Runtime monster state, parallel to NPCInstance."""
    instance_id: str
    template_id: str | None  # For scenario monsters
    repository_name: str | None  # For database monsters
    created_at: datetime
    
    # The template - rename Monster to MonsterSheet for consistency
    sheet: MonsterSheet  # Static template data
    
    # Runtime state (reuse EntityState!)
    state: EntityState  # HP, conditions, inventory, etc.
    
    # Optional location tracking
    current_location_id: str | None = None
    
    def is_alive(self) -> bool:
        return self.state.hit_points.current > 0
```

This achieves:
- ✅ Consistent entity architecture (Character/NPC/Monster all use Instance+Sheet+State)
- ✅ Monsters can persist between encounters
- ✅ Location tracking for wandering monsters
- ✅ Unified EntityState for all creatures
- ✅ Proper separation of template vs runtime data

#### Phase 2: Unified Entity Interface (Completes Solution)
```python
# app/models/interfaces.py
class ICombatEntity(Protocol):
    """Interface for anything that can participate in combat."""
    
    @property
    def name(self) -> str: ...
    
    @property
    def entity_state(self) -> EntityState: ...
    
    def is_alive(self) -> bool: ...
    
    def get_initiative_modifier(self) -> int: ...

# CharacterInstance, NPCInstance, MonsterInstance all implement ICombatEntity

# Simplified CombatParticipant:
class CombatParticipant(BaseModel):
    entity_type: Literal["player", "npc", "monster"]
    entity_id: str  # Instance ID
    initiative: int
    is_active: bool = True
    # No conditions field - read from entity!
    
    def resolve_entity(self, game_state: GameState) -> ICombatEntity:
        """Get the actual entity from game state."""
        if self.entity_type == "player":
            return game_state.character
        elif self.entity_type == "npc":
            return next(n for n in game_state.npcs if n.instance_id == self.entity_id)
        else:  # monster
            return next(m for m in game_state.monsters if m.instance_id == self.entity_id)
```

#### Handler Updates (Works with Both Phases)
```python
# app/events/handlers/character_handler.py
async def handle_update_hp(command: UpdateHPCommand, game_state: GameState):
    if command.target == "player":
        entity = game_state.character
    else:
        # Try all entity types by name
        entity = (
            game_state.get_npc_by_name(command.target) or
            game_state.get_monster_by_name(command.target)
        )
    
    if entity:
        # All entities have .state.hit_points
        old_hp = entity.state.hit_points.current
        # Apply damage/healing...
```

### Implementation Plan

**Step 1: Create MonsterInstance (Required)**
1. Rename `Monster` → `MonsterSheet` (template only; no field changes required)
2. Update `MonsterRepository` to return `MonsterSheet` (imports/generics/return types)
3. Update scenario types and services to use `MonsterSheet` (ScenarioMonster, ScenarioService)
4. Implement `MonsterInstance` with `sheet: MonsterSheet` + `state: EntityState`
5. Change `GameState.monsters` → `list[MonsterInstance]`
6. Update `SaveManager` to store under `instances/monsters/{instance_id}.json` and remove legacy `monsters/` folder
7. Update spawn/combat handlers to create `MonsterInstance`

**Step 2: Add Entity Interface (Recommended)**
1. Define `ICombatEntity` protocol
2. Update `CombatParticipant` to use entity IDs
3. Update handlers to work with unified interface
4. Remove condition duplication from `CombatParticipant`

### Why This Fully Fixes the Problem

**Phase 1 alone fixes:**
- ✅ Monster damage through tools (entities have unified state)
- ✅ Consistent architecture (all entities use Instance pattern)
- ✅ Runtime/template separation

**Phase 1 + 2 together fix:**
- ✅ Fragile name-based resolution (use IDs)
- ✅ Condition synchronization (single source of truth)
- ✅ Extensibility for future features
- ✅ Type-safe entity handling

### Risk Assessment
- No backward compatibility for saves (explicitly accepted)
- Current state blocks monster damage until Phase 1 merges
- Name-based entity resolution remains fragile until Phase 2 (ids)
- Condition duplication risk removed by dropping `CombatParticipant.conditions`

---

## Implementation Priority [REVISED]

### Phase 1: Entity Architecture Fix (CRITICAL - Blocks Combat)
**Issue 5: Entity Architecture and Combat Integration**
1. **MonsterInstance Implementation**
   - Rename `Monster` → `MonsterSheet` across codebase
   - Create `MonsterInstance` model with `sheet` + `state`
   - Update `GameState.monsters` to use `MonsterInstance`
   - Update save/load to use `instances/monsters/`
   - Update spawn handlers to create instances
   - Extend HP/condition handlers to support monsters

2. **Unified Entity Interface**
   - Define `ICombatEntity` protocol
   - Update `CombatParticipant` to use entity IDs
   - Remove `conditions` from `CombatParticipant`
   - Update all handlers for unified interface

### Phase 2: Combat System Completion
1. Implement turn management tools (`next_turn`, `end_combat`)
2. Add corresponding event-bus commands
3. Extend `CombatState` for turn order display
4. Resolve conditions source of truth (entity state only)

### Phase 3: Core Fixes
1. Remove duplicate `set_quest_flag` method
2. Simplify ContextService - remove IScenarioService dependency
3. Add ChangeLocation connection/requirements validation
4. Implement NPC location queries in GameState
5. Remove `npc_ids` from location JSON files

### Phase 4: Model Improvements
1. Add NPC movement tool and handler
2. Add lightweight repository reverse lookups
3. Document `unknown-location` sentinel pattern
4. Consider removing `ScenarioSheet.id` default

### Phase 5: Polish (Defer to MVP2)
1. Review SSE events utility
2. Simplify narrative formatting
3. Plan equipment slot system
4. Consider random encounters

---

## Testing Strategy [REVISED]

### Phase 1 Tests (Entity Architecture)
- Repository returns `MonsterSheet` types correctly
- Save/load of `MonsterInstance` under `instances/monsters/`
- Monster damage/healing through tools
- Monster conditions add/remove through tools
- Combat with mixed entity types (player, NPC, monster)
- Entity ID resolution in CombatParticipant
- Conditions read from entity state (no duplication)

### Phase 2 Tests (Combat System)
- Turn advancement with `next_turn` tool
- Combat end with `end_combat` tool
- Turn order display formatting
- Initiative sorting with mixed entities
- Combat state persistence

### Phase 3 Tests (Core Fixes)
- ContextService without IScenarioService
- ChangeLocation validation (connections/requirements)
- NPC location queries
- Quest flag operations

### Phase 4 Tests (Model Improvements)
- NPC movement between locations
- Repository reverse lookups
- Unknown-location handling

### Manual Testing Required
- Full combat encounter from start to finish
- Monster taking damage and dying
- Mixed combat with player, NPCs, and monsters
- Save/load game with active monsters
- Combat turn progression
