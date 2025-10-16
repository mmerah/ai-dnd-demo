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
**Status**: ✅ Completed | **Estimated**: 3 hours | **Actual**: 0.5 hours

### Task 3.1: Update Combat Initialization
- **Status**: ✅ Completed
- **Files**:
  - `app/interfaces/services/game/combat_service.py`
  - `app/services/game/combat_service.py`
  - `app/events/handlers/combat_handler.py`
  - `app/container.py`
- **Checklist**:
  - [x] Added ensure_party_in_combat to ICombatService interface
  - [x] Implemented ensure_party_in_combat in CombatService
  - [x] Injected IPartyService into CombatService constructor
  - [x] Updated container to inject party_service
  - [x] Called ensure_party_in_combat in StartCombatCommand handler
  - [x] Called ensure_party_in_combat in StartEncounterCombatCommand handler
  - [x] Skip duplicates (idempotent)

### Task 3.2: Stop Auto-Play for Allies
- **Status**: ✅ Completed
- **File**: `app/services/game/combat_service.py`
- **Checklist**:
  - [x] should_auto_continue returns False for ALLY
  - [x] should_auto_end_combat checks only ENEMY
  - [x] Tests updated and verified

### Test Coverage Added
- **Files**: `tests/unit/services/game/test_combat_service.py`, `tests/unit/events/handlers/test_combat_handler.py`
- **New tests**:
  - `test_ensure_party_in_combat` - verifies party members added as ALLY
  - `test_should_auto_continue_false_for_ally` - verifies ALLYs don't auto-continue
  - `test_should_auto_end_combat_ignores_allies` - verifies combat ends when no enemies remain
  - `test_start_combat_includes_party_members` - verifies handler integration
- **Total**: 218 tests passing (4 new tests added)

---

## Phase 4: Combat Suggestions (Reuse Existing)
**Status**: ✅ Completed | **Estimated**: 4 hours | **Actual**: 1.5 hours

### Task 4.1: Combat Suggestion Model
- **Status**: ✅ Completed
- **File**: `app/models/combat.py`
- **Checklist**:
  - [x] CombatSuggestion model created
  - [x] Fields: suggestion_id, npc_id, npc_name, action_text

### Task 4.2: Generate Suggestions in Orchestrator
- **Status**: ✅ Completed
- **File**: `app/services/ai/orchestrator/combat_loop.py`
- **Checklist**:
  - [x] Check for ALLY faction
  - [x] Get NPC agent via lifecycle service
  - [x] Prompt for combat action
  - [x] Create CombatSuggestion
  - [x] Broadcast via SSE (no storage needed - KISS)
  - [x] DO NOT auto-execute

### Task 4.3: SSE Event for Suggestions
- **Status**: ✅ Completed
- **Files**:
  - `app/models/sse_events.py`
  - `app/services/ai/message_service.py`
  - `app/interfaces/services/ai.py`
  - `app/events/commands/broadcast_commands.py`
  - `app/events/handlers/broadcast_handler.py`
- **Checklist**:
  - [x] SSEEventType.COMBAT_SUGGESTION added
  - [x] CombatSuggestionData model added
  - [x] send_combat_suggestion method added to IMessageService and MessageService
  - [x] BroadcastCombatSuggestionCommand created
  - [x] BroadcastHandler updated to handle combat suggestions

---

## Phase 5: Tools for Party Management
**Status**: ✅ Completed | **Estimated**: 2 hours | **Actual**: 0.5 hours

### Task 5.1: Create Party Tools
- **Status**: ✅ Completed
- **File**: `app/tools/party_tools.py`
- **Checklist**:
  - [x] add_party_member tool created
  - [x] remove_party_member tool created
  - [x] Policy: block during combat
  - [x] Policy: block NPC agents
  - [x] Uses @tool_handler decorator

### Task 5.2: Register with Narrative Agent
- **Status**: ✅ Completed
- **File**: `app/agents/narrative/agent.py`
- **Checklist**:
  - [x] Import party tools
  - [x] Add to tool list
  - [x] Test tool usage

---

## Phase 6: API Layer (KISS)
**Status**: ✅ Completed | **Estimated**: 2 hours | **Actual**: 0.5 hours

### Task 6.1: Suggestion Acceptance Endpoint
- **Status**: ✅ Completed
- **Files**:
  - `app/api/routers/game.py`
  - `app/models/requests.py`
- **Checklist**:
  - [x] POST /api/game/{game_id}/combat/suggestion/accept
  - [x] Accept suggestion data from client (no server-side storage needed)
  - [x] Send to combat agent via background task
  - [x] Combat agent calls NextTurnCommand tool to advance turn
  - [x] Request/Response models created
  - [x] Type checking passes (mypy --strict)
  - [x] Linting passes (ruff)

### Task 6.2: Transient Suggestion Storage
- **Status**: ❌ Not Needed (Design Decision)
- **Rationale**: Following KISS principle from Phase 4 implementation
- **Explanation**:
  - Client receives complete `CombatSuggestion` object via SSE (includes: suggestion_id, npc_id, npc_name, action_text)
  - Client sends all data back in accept request - no server-side storage required
  - Simpler architecture, less state management, more robust
  - Consistent with stateless API design patterns

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
| Phase 3 | ✅ Completed | 2 | 2 | 100% |
| Phase 4 | ✅ Completed | 3 | 3 | 100% |
| Phase 5 | ✅ Completed | 2 | 2 | 100% |
| Phase 6 | ✅ Completed | 2 | 1 | 100% |
| Phase 7 | ⬜ Not Started | 2 | 0 | 0% |
| Phase 8 | ⬜ Not Started | 3 | 0 | 0% |
| Phase 9 | ⬜ Not Started | 3 | 0 | 0% |
| **Total** | **🟨 In Progress** | **22** | **13** | **59%** |

**Estimated Total**: 30 hours
**Actual Total**: 5.0 hours
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

- **Phase 3 (2025-10-16)**: Successfully integrated party members into combat system
  - Added `ensure_party_in_combat()` method to `ICombatService` interface
  - Implemented method in `CombatService` with proper location checking and idempotency
  - Injected `IPartyService` into `CombatService` via container (proper DI)
  - Updated both `StartCombatCommand` and `StartEncounterCombatCommand` handlers
  - Modified `should_auto_continue()` to return False for ALLY faction (requires player confirmation)
  - Modified `should_auto_end_combat()` to only check for ENEMY faction (not all non-players)
  - Faction inference already working correctly (NPCs in party get ALLY faction automatically)
  - Pattern follows existing `ensure_player_in_combat()` design (consistency)

- **Phase 4 (2025-10-16)**: Successfully implemented combat suggestions for allied NPCs
  - Created `CombatSuggestion` model in `app/models/combat.py` with suggestion_id, npc_id, npc_name, action_text
  - Added `SSEEventType.COMBAT_SUGGESTION` enum value
  - Created `CombatSuggestionData` SSE event model in `app/models/sse_events.py`
  - Added `send_combat_suggestion()` to `IMessageService` interface and `MessageService` implementation
  - Created `BroadcastCombatSuggestionCommand` in `app/events/commands/broadcast_commands.py`
  - Updated `BroadcastHandler` to handle combat suggestion broadcasts
  - Modified `combat_loop.run()` to detect ALLY turns and generate suggestions:
    - Checks current turn faction for ALLY
    - Retrieves NPC agent via `agent_lifecycle_service`
    - Prompts NPC agent for combat action suggestion
    - Broadcasts suggestion via SSE using event bus
    - Breaks loop to wait for player decision (no auto-continue)
  - Updated `orchestrator_service.py` to pass `agent_lifecycle_service` to combat_loop
  - **No server-side storage needed** - client receives suggestion via SSE and sends it back in API request (KISS principle)
  - All 218 tests passing
  - Type safety verified (mypy --strict)

- **Phase 5 (2025-10-16)**: Successfully implemented party management tools for narrative agent
  - Created `app/tools/party_tools.py` with two tools:
    - `add_party_member(npc_id)` - wraps AddPartyMemberCommand
    - `remove_party_member(npc_id)` - wraps RemovePartyMemberCommand
  - Both tools use @tool_handler decorator (DRY principle)
  - Policy enforcement implemented at service layer (KISS):
    - Added combat validation in `PartyService.add_member()` and `PartyService.remove_member()`
    - NPC agents already blocked via existing `NPC_ALLOWED_TOOLS` whitelist in ActionService
    - No special PARTY_TOOLS category needed - leverages existing architecture
  - Registered both tools with narrative agent in `app/agents/narrative/agent.py`
  - Added comprehensive tests for combat blocking behavior
  - All 220 tests passing (12 party tests total)
  - Type safety verified (mypy --strict)
  - Clean lint (ruff)
  - **Design decision**: Combat blocking enforced at PartyService (business logic) rather than ActionService (agent policy) because:
    - Orchestrator already prevents narrative agent from running during combat
    - NPC agents automatically blocked by existing whitelist mechanism
    - Simpler, more maintainable approach following KISS principle

- **Phase 6 (2025-10-16)**: Successfully implemented API layer for combat suggestions (stateless design)
  - Created request/response models in `app/models/requests.py`:
    - `AcceptCombatSuggestionRequest` - receives suggestion data from client
    - `AcceptCombatSuggestionResponse` - confirms acceptance
  - Added endpoint `POST /api/game/{game_id}/combat/suggestion/accept` in `app/api/routers/game.py`:
    - Validates combat is active
    - Formats message: "{npc_name} performs: {action_text}"
    - Uses background task pattern (same as player actions)
    - Combat agent narrates the action and calls NextTurnCommand tool
    - Combat loop continues with auto-play if needed
  - **Task 6.2 (Transient Storage) NOT NEEDED** - Critical design decision:
    - Client receives complete CombatSuggestion via SSE (suggestion_id, npc_id, npc_name, action_text)
    - Client sends all data back in request - no server-side state needed
    - Follows KISS principle: stateless API, simpler architecture, more robust
    - Reduces complexity and potential for state synchronization bugs
    - Consistent with RESTful design patterns
  - Type safety verified (mypy --strict)
  - Clean lint (ruff)
  - Implementation time: 0.5 hours (significantly under 2 hour estimate due to KISS approach)

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