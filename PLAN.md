# NPC Party System - Implementation Plan

## Overview
Implementation plan for adding NPC party support to the D&D AI Dungeon Master, following SOLID, DRY, KISS, and FAIL-FAST principles. Major NPCs can join the party through natural dialogue, auto-follow between locations, and participate as allies in combat with player confirmation.

## Design Decisions
- **Consent**: Inferred from agent tool usage (KISS principle)
- **Combat Suggestions**: Simple text descriptions from NPC perspective
- **UI**: New Party section with selectable member cards replacing static character sheet
- **NPC Agent**: Reuse IndividualMindAgent for suggestions (DRY principle)
- **Party Size**: Constant in code (4 members max)
- **Death/Unconscious**: Members remain in party but marked as unconscious/dead
- **Location Requirements**: NPCs must be at same location to join party
- **Suggestion Timeout**: Unlimited time for player decisions
- **Persistence**: Automatic via GameState (no special handling needed)
- **Dialogue**: Only addressed NPC responds when in party
- **Formation**: No positioning system (out of scope)

## Current State Analysis

### Already Implemented
- ✅ `PartyState` model with validation
- ✅ `GameState.party` integration
- ✅ `CombatFaction` enum with ALLY support
- ✅ Combat faction inference checks party membership
- ✅ NPC agent system (IndividualMindAgent)
- ✅ Event bus and SSE infrastructure

### Missing Components
- ❌ Party service layer
- ❌ Party commands/handlers/tools
- ❌ Combat suggestion for allied NPCs
- ❌ Auto-follow logic
- ❌ Combat loop stops for allies
- ❌ Frontend party UI overhaul
- ❌ API endpoints for suggestions

## Phase 1: Backend Party Service (SOLID Foundation)

### Task 1.1: Create IPartyService Interface
**Context**: `app/interfaces/services/game/*.py`, `app/models/party.py`
**Rationale**: Single responsibility - define party management contract
**Implementation**:
- Create `app/interfaces/services/game/party_service.py`
- Methods:
  - `add_member(game_state, npc_id) -> None` (fail-fast on invalid)
  - `remove_member(game_state, npc_id) -> None` (fail-fast on not found)
  - `is_member(game_state, npc_id) -> bool` (check membership)
  - `list_members(game_state) -> list[NPCInstance]` (get all party NPCs)
  - `get_follow_commands(game_state, to_location_id) -> list[MoveNPCCommand]`
  - `is_eligible(npc: NPCInstance) -> bool` (major-only check)

### Task 1.2: Implement PartyService
**Context**: Interface from 1.1, `app/services/game/location_service.py` patterns
**Rationale**: Encapsulate party logic with fail-fast validation
**Implementation**:
- Create `app/services/game/party_service.py`
- Validate: major NPCs only, capacity=4, no duplicates, same location required
- Check NPC location matches player location in `add_member`
- Raise immediately on violations (fail-fast)
- `get_follow_commands`: return commands for members not at destination
- Dead/unconscious NPCs remain in party (check `is_alive()` for display)

### Task 1.3: Party Commands and Handler
**Context**: `app/events/commands/location_commands.py`, `app/events/handlers/location_handler.py`
**Rationale**: Event-sourced mutations with single handler responsibility
**Implementation**:
- Create `app/events/commands/party_commands.py`:
  - `AddPartyMemberCommand(npc_id)`
  - `RemovePartyMemberCommand(npc_id)`
- Create `app/events/handlers/party_handler.py`:
  - Delegate to PartyService (DRY)
  - Broadcast game updates
  - Single responsibility: party state mutations

### Task 1.4: Wire in Container
**Context**: `app/container.py`
**Rationale**: Dependency injection for testability
**Implementation**:
- Add `party_service` cached property
- Register PartyHandler with event bus
- No circular dependencies

## Phase 2: Movement Integration (DRY)

### Task 2.1: Integrate Follow Logic
**Context**: `app/events/handlers/location_handler.py`, PartyService from Phase 1
**Rationale**: Centralize follow logic in one place (DRY)
**Implementation**:
- In LocationHandler's ChangeLocationCommand:
  - After player moves successfully, get follow commands via `party_service.get_follow_commands()`
  - Add commands to result.commands
- No duplication - PartyService handles logic

## Phase 3: Combat Integration

### Task 3.1: Update Combat Initialization
**Context**: `app/events/handlers/combat_handler.py`, `app/services/game/combat_service.py`
**Rationale**: Auto-add party as allies (single source of truth for faction)
**Implementation**:
- In StartCombatCommand/StartEncounterCommand handler:
  - Get party members at current location
  - Add with faction=ALLY (already inferred by CombatService)
- Skip duplicates (idempotent)

### Task 3.2: Stop Auto-Play for Allies
**Context**: `app/services/game/combat_service.py`, `app/interfaces/services/game/combat_service.py`
**Rationale**: Allied NPCs need player confirmation (not auto-play)
**Implementation**:
- `should_auto_continue()`: return False if current turn faction == ALLY
- `should_auto_end_combat()`: only check faction == ENEMY
- KISS: Simple boolean checks, no complex logic

## Phase 4: Combat Suggestions (Reuse Existing)

### Task 4.1: Combat Suggestion Model
**Context**: `app/models/ai_response.py`
**Rationale**: Simple data structure for suggestions (KISS)
**Implementation**:
- Create `app/models/combat_suggestion.py`:
```python
class CombatSuggestion(BaseModel):
    suggestion_id: str  # For acceptance tracking
    npc_id: str
    npc_name: str
    action_text: str  # Simple description from NPC perspective
```

### Task 4.2: Generate Suggestions in Orchestrator
**Context**: `app/services/ai/orchestrator/combat_loop.py`, `app/services/ai/agent_lifecycle_service.py`
**Rationale**: Reuse IndividualMindAgent (DRY), simple text generation (KISS)
**Implementation**:
- In combat_loop.run():
  - Check if current turn is ALLY faction
  - Get NPC agent via agent_lifecycle_service (existing)
  - Prompt: "What combat action do you take? (Describe briefly)"
  - Capture response as suggestion text
  - Create CombatSuggestion, store transiently
  - Broadcast via SSE
  - DO NOT execute - wait for player

### Task 4.3: SSE Event for Suggestions
**Context**: `app/models/sse_events.py`, `app/services/ai/message_service.py`
**Rationale**: Consistent with existing SSE patterns (DRY)
**Implementation**:
- Add `SSEEventType.COMBAT_SUGGESTION`
- Add to MessageService.send_combat_suggestion()
- Reuse existing SSE infrastructure

## Phase 5: Tools for Party Management

### Task 5.1: Create Party Tools
**Context**: `app/tools/decorators.py`, commands from Phase 1
**Rationale**: Single responsibility - agent interface to party system
**Implementation**:
- Create `app/tools/party_tools.py`:
  - `add_party_member(npc_id)` - wraps AddPartyMemberCommand
  - `remove_party_member(npc_id)` - wraps RemovePartyMemberCommand
- Use @tool_handler decorator (DRY)
- Policy enforcement:
  - Block during combat (check game_state.combat.is_active)
  - Block NPC agents from calling these tools (check agent_type)
  - Only narrative agent can use party tools
- No complex logic - delegate to commands

### Task 5.2: Register with Narrative Agent
**Context**: `app/agents/narrative/agent.py`
**Rationale**: Enable party management in narrative context
**Implementation**:
- Import party tools
- Add to tool list
- No prompt changes needed (agent infers usage)

## Phase 6: API Layer (KISS)

### Task 6.1: Suggestion Acceptance Endpoint
**Context**: `app/api/routers/game_router.py`, `app/api/player_actions.py`
**Rationale**: Simple endpoint for UI interaction
**Implementation**:
- Add `POST /api/game/{game_id}/combat/suggestion/accept`
- Retrieve stored suggestion
- Send simple message to combat agent: "{npc_name} performs: {action_text}"
- Call NextTurnCommand
- No complex action parsing (KISS)

### Task 6.2: Transient Suggestion Storage
**Context**: `app/services/game/game_state_manager.py`
**Rationale**: Simple in-memory storage (no persistence needed)
**Implementation**:
- Add `current_combat_suggestion: CombatSuggestion | None` to manager
- Set when generated, clear when accepted/rejected
- Single source of truth

## Phase 7: Frontend - Party UI Overhaul

### Task 7.1: Redesign Character Sheet as Party Section
**Context**: `frontend/index.html`, `frontend/app.js`, `frontend/style.css`
**Rationale**: Unified party view with selectable members
**UI Design**:
```
Party Section (Left Panel):
┌──────────────────────────────────┐
│ PARTY (3/4)                      │
├──────────────────────────────────┤
│ [Player Card] ←selected          │
│ Aldric | 28/35 HP | AC 16       │
│ Lv 5 Fighter (Human)             │
│ 🟢 Healthy                       │
├──────────────────────────────────┤
│ [NPC Card]                       │
│ Lyra | 24/24 HP | AC 14         │
│ Lv 4 Ranger (Elf)               │
│ 🟢 Healthy                       │
├──────────────────────────────────┤
│ [NPC Card]                       │
│ Thorin | 0/42 HP | AC 18        │
│ Lv 5 Cleric (Dwarf)             │
│ 💀 Unconscious                   │
└──────────────────────────────────┘

[Selected Member Details Below]
- Full character/NPC sheet
- Abilities, inventory, etc.
```

**Implementation**:
- Replace static character sheet with dynamic party section
- Create party member cards (player + NPCs)
- Click card to show full details below
- Highlight selected member
- Show HP/AC/conditions on cards

### Task 7.2: Frontend State Management
**Context**: `frontend/app.js` gameState handling
**Rationale**: Single source of truth for party display
**Implementation**:
- Parse party.member_ids from gameState
- Build party display data combining player + party NPCs
- Update on game_update events
- Track selected member for detail view

## Phase 8: Combat Suggestion UI

### Task 8.1: Add Suggestion Display
**Context**: `frontend/index.html` combat section
**Rationale**: Clear, non-intrusive suggestion display
**Implementation**:
- Add suggestion card in combat area:
```html
<div class="combat-suggestion">
  <div class="suggestion-header">
    <img src="npc-avatar"> Lyra's Turn
  </div>
  <div class="suggestion-text">
    "I'll fire my bow at the wounded goblin"
  </div>
  <div class="suggestion-actions">
    <button onclick="acceptSuggestion()">Use This</button>
    <button onclick="overrideSuggestion()">Do Something Else</button>
  </div>
</div>
```

### Task 8.2: Handle SSE Events
**Context**: `frontend/app.js` SSE handlers
**Rationale**: Consistent with existing event handling (DRY)
**Implementation**:
- Add listener for 'combat_suggestion'
- Display suggestion card
- Store suggestion_id for acceptance
- Clear on acceptance/override

### Task 8.3: Implement Actions
**Context**: `frontend/app.js` API calls
**Rationale**: Simple user actions (KISS)
**Implementation**:
- Accept: POST to acceptance endpoint
- Override: Hide suggestion, enable chat for manual input
- Handle errors with existing patterns

## Phase 9: Testing Strategy

### Task 9.1: Unit Tests
**Focus**: Service layer logic
**Coverage**:
- PartyService: validation, follow generation
- Combat modifications: faction checks
- Fast, isolated tests

### Task 9.2: Integration Tests
**Focus**: End-to-end flows
**Coverage**:
- Party join via dialogue
- Location change with follows
- Combat with allies
- Suggestion flow

### Task 9.3: Manual Testing Checklist
- [ ] Add NPC to party via dialogue
- [ ] Party follows on location change
- [ ] Party members join combat as allies
- [ ] Allied turn shows suggestion
- [ ] Accept/override suggestion works
- [ ] Party UI updates correctly
- [ ] Selected member details display

## Implementation Order & Time Estimates

1. **Phase 1**: Backend Party Service (4 hours)
2. **Phase 2**: Movement Integration (2 hours)
3. **Phase 3**: Combat Integration (3 hours)
4. **Phase 4**: Combat Suggestions (4 hours)
5. **Phase 5**: Party Tools (2 hours)
6. **Phase 6**: API Layer (2 hours)
7. **Phase 7**: Frontend Party UI (6 hours)
8. **Phase 8**: Suggestion UI (3 hours)
9. **Phase 9**: Testing (4 hours)

**Total Estimate**: ~30 hours

## Key Principles Applied

**SOLID**:
- Single Responsibility: Each service/handler has one job
- Open/Closed: Extend via new handlers, don't modify existing
- Interface Segregation: IPartyService is focused
- Dependency Inversion: Depend on interfaces

**DRY**:
- Reuse IndividualMindAgent for suggestions
- Reuse existing event/SSE infrastructure
- No duplicate validation logic

**KISS**:
- Simple text suggestions (no complex action parsing)
- Consent inferred from tool usage
- Basic in-memory suggestion storage

**FAIL-FAST**:
- Immediate validation in PartyService
- Raise exceptions on invalid operations
- No silent failures

## Success Metrics

- ✅ NPCs join party through natural dialogue
- ✅ Party auto-follows between locations
- ✅ Allied NPCs pause combat for confirmation
- ✅ Clean, intuitive party UI
- ✅ No regression in existing features
- ✅ All tests passing
- ✅ Code follows established patterns