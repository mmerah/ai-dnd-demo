# NPC Party System - Implementation Progress

Track implementation progress against PLAN.md. Update status as tasks are completed.

## Status Legend
- ⬜ Not Started
- 🟨 In Progress
- ✅ Completed
- ❌ Blocked

---

## Phase 1: Backend Party Service (SOLID Foundation)
**Status**: ⬜ Not Started | **Estimated**: 4 hours | **Actual**: -

### Task 1.1: Create IPartyService Interface
- **Status**: ⬜ Not Started
- **File**: `app/interfaces/services/game/party_service.py`
- **Checklist**:
  - [ ] Interface created
  - [ ] add_member method defined
  - [ ] remove_member method defined
  - [ ] is_member method defined
  - [ ] list_members method defined
  - [ ] get_follow_commands method defined
  - [ ] is_eligible method defined

### Task 1.2: Implement PartyService
- **Status**: ⬜ Not Started
- **File**: `app/services/game/party_service.py`
- **Checklist**:
  - [ ] Service class created
  - [ ] Major NPC validation
  - [ ] Capacity validation (max 4)
  - [ ] Same location validation
  - [ ] Duplicate prevention
  - [ ] Follow command generation
  - [ ] Dead/unconscious handling

### Task 1.3: Party Commands and Handler
- **Status**: ⬜ Not Started
- **Files**:
  - `app/events/commands/party_commands.py`
  - `app/events/handlers/party_handler.py`
- **Checklist**:
  - [ ] AddPartyMemberCommand created
  - [ ] RemovePartyMemberCommand created
  - [ ] PartyHandler created
  - [ ] Handler delegates to PartyService
  - [ ] Broadcasts game updates

### Task 1.4: Wire in Container
- **Status**: ⬜ Not Started
- **File**: `app/container.py`
- **Checklist**:
  - [ ] party_service cached property added
  - [ ] PartyHandler registered with event bus
  - [ ] Imports added

---

## Phase 2: Movement Integration (DRY)
**Status**: ⬜ Not Started | **Estimated**: 2 hours | **Actual**: -

### Task 2.1: Integrate Follow Logic
- **Status**: ⬜ Not Started
- **File**: `app/events/handlers/location_handler.py`
- **Checklist**:
  - [ ] Import PartyService
  - [ ] Call get_follow_commands after player move
  - [ ] Add follow commands to result
  - [ ] Test follow behavior

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
| Phase 1 | ⬜ Not Started | 4 | 0 | 0% |
| Phase 2 | ⬜ Not Started | 1 | 0 | 0% |
| Phase 3 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 4 | ⬜ Not Started | 3 | 0 | 0% |
| Phase 5 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 6 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 7 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 8 | ⬜ Not Started | 3 | 0 | 0% |
| Phase 9 | ⬜ Not Started | 3 | 0 | 0% |
| **Total** | **⬜ Not Started** | **22** | **0** | **0%** |

**Estimated Total**: 30 hours
**Actual Total**: 0 hours
**Started**: Not yet
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
- Add notes here during implementation
- Document any deviations from plan
- Record important decisions

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