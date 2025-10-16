# NPC Party System - Implementation Progress

Track implementation progress against PLAN.md. Update status as tasks are completed.

## Status Legend
- ⬜ Not Started
- 🟨 In Progress
- ✅ Completed
- ❌ Blocked

---

## Phase 1: Backend Party Service (SOLID Foundation)
**Status**: ✅ Completed | **Estimated**: 4 hours | **Actual**: 1.5 hours

### Task 1.1: Create IPartyService Interface
- **Status**: ✅ Completed
- **File**: `app/interfaces/services/game/party_service.py`
- **Checklist**:
  - [x] Interface created
  - [x] add_member method defined
  - [x] remove_member method defined
  - [x] is_member method defined
  - [x] list_members method defined
  - [x] get_follow_commands method defined
  - [x] is_eligible method defined

### Task 1.2: Implement PartyService
- **Status**: ✅ Completed
- **File**: `app/services/game/party_service.py`
- **Checklist**:
  - [x] Service class created
  - [x] Major NPC validation
  - [x] Capacity validation (max 4)
  - [x] Same location validation
  - [x] Duplicate prevention
  - [x] Follow command generation
  - [x] Dead/unconscious handling

### Task 1.3: Party Commands and Handler
- **Status**: ✅ Completed
- **Files**:
  - `app/events/commands/party_commands.py`
  - `app/events/handlers/party_handler.py`
- **Checklist**:
  - [x] AddPartyMemberCommand created
  - [x] RemovePartyMemberCommand created
  - [x] PartyHandler created
  - [x] Handler delegates to PartyService
  - [x] Broadcasts game updates

### Task 1.4: Wire in Container
- **Status**: ✅ Completed
- **File**: `app/container.py`
- **Checklist**:
  - [x] party_service cached property added
  - [x] PartyHandler registered with event bus
  - [x] Imports added

---

## Phase 2: Movement Integration (DRY)
**Status**: ✅ Completed | **Estimated**: 2 hours | **Actual**: 0.5 hours

### Task 2.1: Integrate Follow Logic
- **Status**: ✅ Completed
- **File**: `app/events/handlers/location_handler.py`
- **Checklist**:
  - [x] Import PartyService
  - [x] Call get_follow_commands after player move
  - [x] Add follow commands to result
  - [x] Test follow behavior

---

## Phase 3: Combat Integration
**Status**: ⬜ Not Started | **Estimated**: 3 hours | **Actual**: -

### Task 3.1: Update Combat Initialization
- **Status**: ⬜ Not Started
- **File**: `app/events/handlers/combat_handler.py`
- **Checklist**:
  - [ ] Import PartyService
  - [ ] Get party members at location
  - [ ] Add party as ALLY faction
  - [ ] Skip duplicates

### Task 3.2: Stop Auto-Play for Allies
- **Status**: ⬜ Not Started
- **File**: `app/services/game/combat_service.py`
- **Checklist**:
  - [ ] should_auto_continue returns False for ALLY
  - [ ] should_auto_end_combat checks only ENEMY
  - [ ] Tests updated

---

## Phase 4: Combat Suggestions (Reuse Existing)
**Status**: ⬜ Not Started | **Estimated**: 4 hours | **Actual**: -

### Task 4.1: Combat Suggestion Model
- **Status**: ⬜ Not Started
- **File**: `app/models/combat_suggestion.py`
- **Checklist**:
  - [ ] CombatSuggestion model created
  - [ ] Fields: suggestion_id, npc_id, npc_name, action_text

### Task 4.2: Generate Suggestions in Orchestrator
- **Status**: ⬜ Not Started
- **File**: `app/services/ai/orchestrator/combat_loop.py`
- **Checklist**:
  - [ ] Check for ALLY faction
  - [ ] Get NPC agent via lifecycle service
  - [ ] Prompt for combat action
  - [ ] Create CombatSuggestion
  - [ ] Store transiently
  - [ ] Broadcast via SSE
  - [ ] DO NOT auto-execute

### Task 4.3: SSE Event for Suggestions
- **Status**: ⬜ Not Started
- **Files**:
  - `app/models/sse_events.py`
  - `app/services/ai/message_service.py`
- **Checklist**:
  - [ ] SSEEventType.COMBAT_SUGGESTION added
  - [ ] send_combat_suggestion method added

---

## Phase 5: Tools for Party Management
**Status**: ⬜ Not Started | **Estimated**: 2 hours | **Actual**: -

### Task 5.1: Create Party Tools
- **Status**: ⬜ Not Started
- **File**: `app/tools/party_tools.py`
- **Checklist**:
  - [ ] add_party_member tool created
  - [ ] remove_party_member tool created
  - [ ] Policy: block during combat
  - [ ] Policy: block NPC agents
  - [ ] Uses @tool_handler decorator

### Task 5.2: Register with Narrative Agent
- **Status**: ⬜ Not Started
- **File**: `app/agents/narrative/agent.py`
- **Checklist**:
  - [ ] Import party tools
  - [ ] Add to tool list
  - [ ] Test tool usage

---

## Phase 6: API Layer (KISS)
**Status**: ⬜ Not Started | **Estimated**: 2 hours | **Actual**: -

### Task 6.1: Suggestion Acceptance Endpoint
- **Status**: ⬜ Not Started
- **File**: `app/api/routers/game_router.py`
- **Checklist**:
  - [ ] POST /api/game/{game_id}/combat/suggestion/accept
  - [ ] Retrieve stored suggestion
  - [ ] Send to combat agent
  - [ ] Call NextTurnCommand

### Task 6.2: Transient Suggestion Storage
- **Status**: ⬜ Not Started
- **File**: `app/services/game/game_state_manager.py`
- **Checklist**:
  - [ ] current_combat_suggestion field added
  - [ ] Set on generation
  - [ ] Clear on acceptance

---

## Phase 7: Frontend - Party UI Overhaul
**Status**: ⬜ Not Started | **Estimated**: 6 hours | **Actual**: -

### Task 7.1: Redesign Character Sheet as Party Section
- **Status**: ⬜ Not Started
- **Files**:
  - `frontend/index.html`
  - `frontend/style.css`
- **Checklist**:
  - [ ] Party section structure created
  - [ ] Party member cards layout
  - [ ] Selected member details area
  - [ ] Card shows: Name, HP/MaxHP, AC, Level, Class, Race, Status
  - [ ] Click handler for selection
  - [ ] Visual selection indicator

### Task 7.2: Frontend State Management
- **Status**: ⬜ Not Started
- **File**: `frontend/app.js`
- **Checklist**:
  - [ ] Parse party.member_ids
  - [ ] Combine player + party NPCs
  - [ ] Track selected member
  - [ ] Update on game_update events
  - [ ] Display member details

---

## Phase 8: Combat Suggestion UI
**Status**: ⬜ Not Started | **Estimated**: 3 hours | **Actual**: -

### Task 8.1: Add Suggestion Display
- **Status**: ⬜ Not Started
- **File**: `frontend/index.html`
- **Checklist**:
  - [ ] Suggestion card HTML structure
  - [ ] Styling for suggestion card
  - [ ] Accept/Override buttons

### Task 8.2: Handle SSE Events
- **Status**: ⬜ Not Started
- **File**: `frontend/app.js`
- **Checklist**:
  - [ ] combat_suggestion event listener
  - [ ] Display suggestion card
  - [ ] Store suggestion_id
  - [ ] Clear on action

### Task 8.3: Implement Actions
- **Status**: ⬜ Not Started
- **File**: `frontend/app.js`
- **Checklist**:
  - [ ] acceptSuggestion function
  - [ ] overrideSuggestion function
  - [ ] API call to accept endpoint
  - [ ] Error handling

---

## Phase 9: Testing Strategy
**Status**: ⬜ Not Started | **Estimated**: 4 hours | **Actual**: -

### Task 9.1: Unit Tests
- **Status**: ⬜ Not Started
- **Files**: `tests/unit/services/game/test_party_service.py`
- **Checklist**:
  - [ ] Test add_member validations
  - [ ] Test remove_member
  - [ ] Test follow generation
  - [ ] Test combat faction checks

### Task 9.2: Integration Tests
- **Status**: ⬜ Not Started
- **Files**: `tests/integration/test_party_flow.py`
- **Checklist**:
  - [ ] Test party join via dialogue
  - [ ] Test location change with follows
  - [ ] Test combat with allies
  - [ ] Test suggestion flow

### Task 9.3: Manual Testing
- **Status**: ⬜ Not Started
- **Checklist**:
  - [ ] Add NPC to party via dialogue
  - [ ] Party follows on location change
  - [ ] Party members join combat as allies
  - [ ] Allied turn shows suggestion
  - [ ] Accept/override suggestion works
  - [ ] Party UI updates correctly
  - [ ] Selected member details display

---

## Overall Progress

| Phase | Status | Tasks | Completed | Progress |
|-------|--------|-------|-----------|----------|
| Phase 1 | ✅ Completed | 4 | 4 | 100% |
| Phase 2 | ✅ Completed | 1 | 1 | 100% |
| Phase 3 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 4 | ⬜ Not Started | 3 | 0 | 0% |
| Phase 5 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 6 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 7 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 8 | ⬜ Not Started | 3 | 0 | 0% |
| Phase 9 | ⬜ Not Started | 3 | 0 | 0% |
| **Total** | **🟨 In Progress** | **22** | **5** | **23%** |

**Estimated Total**: 30 hours
**Actual Total**: 2.0 hours
**Started**: 2025-10-16
**Target Completion**: TBD

---

## Notes & Blockers

### Current Blockers
- None

### Dependencies Verified
- ✅ NPC Agent Extension (already implemented)
- ✅ MessageRole.NPC (exists)
- ✅ NPC_DIALOGUE SSE (exists)
- ✅ dialogue_session state (exists)
- ✅ AgentLifecycleService (exists)

### Implementation Notes
- **Phase 1 (2025-10-16)**: Successfully implemented backend party service with full SOLID compliance
  - Interface-first design in `app/interfaces/services/game/party_service.py`
  - Service implementation with fail-fast validation in `app/services/game/party_service.py`
  - Commands and handler following existing patterns
  - Container wiring with zero circular dependencies
  - All type checks pass (mypy --strict)
  - Container loads successfully with party_service accessible

- **Phase 2 (2025-10-16)**: Successfully integrated follow logic into location changes
  - Injected `IPartyService` into `LocationHandler` constructor
  - Added follow command generation after player location change in `ChangeLocationCommand` handling
  - PartyService handles all follow logic (DRY principle maintained)
  - Follow commands added to `CommandResult.follow_up_commands` for event bus processing
  - Comprehensive test added: `test_change_location_generates_follow_commands`
  - All 214 tests pass
  - Type safety verified (mypy --strict)
  - Linter clean (ruff)

---

## How to Update This Document

1. When starting a task: Change status to 🟨 In Progress
2. When completing a task:
   - Change status to ✅ Completed
   - Check off all checklist items
   - Update phase actual hours
3. If blocked: Change status to ❌ Blocked and add note in Blockers section
4. Update Overall Progress table percentages
5. Add any important notes or decisions in Notes section

Remember: This document is for tracking progress. Keep PLAN.md as the source of truth for requirements.