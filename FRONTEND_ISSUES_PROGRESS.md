# Frontend-v2 Issues Progress Tracker

**Last Updated**: 2025-11-06
**Status**: ALL P0 ISSUES COMPLETED! Ready for P1 issues.

## Completed Fixes ✅

### P0 Issues

#### Issue #1 & #4: Exit/Leave Game Button + Header Bar ✅
**Status**: COMPLETED
**Files Modified**:
- Created: `frontend-v2/src/components/header/HeaderBar.ts`
- Modified: `frontend-v2/src/screens/GameInterfaceScreen.ts`
- Modified: `frontend-v2/src/screens/ScreenManager.ts`
- Modified: `frontend-v2/styles/main.css`

**Implementation**:
- Added full header bar component with:
  - 🚪 Exit/Leave game button with confirmation dialog
  - 📍 Current location display
  - 🛡️ Danger level indicator (color-coded with animation for extreme)
  - 🕐 Game time display (Day X, HH:MM)
  - ⚔️ Combat indicator (shows/hides based on combat state)
  - 🤖 Active agent indicator
  - 💾 Save button (shows auto-save message)
- Integrated into GameInterfaceScreen layout
- Exit button navigates back to game list

**Validation**: TypeScript compiles without errors

---

#### Issue #3: Party Member Selection ✅
**Status**: COMPLETED
**Files Modified**:
- Modified: `frontend-v2/src/components/character-sheet/CharacterSheetPanel.ts`
- Modified: `frontend-v2/src/components/inventory/InventoryPanel.ts`

**Implementation**:
- Fixed CharacterSheetPanel to display selected party member (player or NPC)
  - Added `getSelectedMember()` helper method
  - Added `isNPC()` type guard
  - Subscribe to `selectedMemberId$` changes
  - Properly handles NPC sheet structure vs character sheet
- Fixed InventoryPanel to display selected member's inventory
  - Added `getSelectedMember()` helper method
  - Subscribe to `selectedMemberId$` changes
  - Shows currency, equipment, and items for selected member
- PartyPanel already had correct selection handling (no changes needed)

**Validation**: TypeScript compiles without errors

---

#### Issue #28: Missing SSE Event Types ✅
**Status**: COMPLETED
**Priority**: P0 - CRITICAL

**Implementation**:
- Added 8 missing SSE event types to `frontend-v2/src/types/sse.ts`:
  - ✅ `connected` - Connection confirmation
  - ✅ `narrative` - Non-streaming narrative text
  - ✅ `initial_narrative` - Opening scene for new games
  - ✅ `tool_result` - Tool result display
  - ✅ `npc_dialogue` - NPC speech rendering
  - ✅ `policy_warning` - Policy violation warnings
  - ✅ `combat_suggestion` - Allied NPC action suggestions
  - ✅ `scenario_info` - Full scenario data
- Created TypeScript interfaces for each event type with proper data structures
- Updated `SseService.ts` to register event listeners for all new types
- All event types now properly handled by the SSE service

**Files Modified**:
- `frontend-v2/src/types/sse.ts` - Added 8 event types with interfaces
- `frontend-v2/src/services/sse/SseService.ts` - Registered handlers for new events

**Validation**: TypeScript compiles without errors

---

#### Issue #29: Chat Message Types Limited ✅
**Status**: COMPLETED
**Priority**: P0 - CRITICAL

**Implementation**:
- Created new `ChatDisplayMessage` type system in `frontend-v2/src/types/chat.ts`:
  - Supports 10 message types: user, assistant, system, tool, tool-result, npc, policy-warning, loading, error, success
  - Includes metadata field for type-specific data (tool names, parameters, NPC info, etc.)
  - Converter function to transform conversation history Messages to ChatDisplayMessages
- Completely refactored `ChatMessage.ts` component:
  - ✅ `tool` - Tool calls with dice icon and formatted parameters
  - ✅ `tool-result` - Tool results with chart icon and formatted output
  - ✅ `npc` - NPC dialogue with speaker name in separate element
  - ✅ `policy-warning` - Policy warnings with warning icon and agent/tool details
  - ✅ `loading` - Loading state messages
  - ✅ `error` - Error messages
  - ✅ `success` - Success notifications
  - Special formatting for dice roll parameters (ability, skill, DC, purpose)
  - Markdown rendering for assistant messages
- Updated `ChatPanel.ts` to use new ChatDisplayMessage type
  - Converts conversation history Messages to display messages
  - Ready to handle real-time SSE event messages

**Files Modified**:
- Created: `frontend-v2/src/types/chat.ts` - New display message type system
- Rewritten: `frontend-v2/src/components/chat/ChatMessage.ts` - Full support for all message types
- Updated: `frontend-v2/src/components/chat/ChatPanel.ts` - Uses new type system

**Validation**: TypeScript compiles without errors

---

#### Issue #6: Combat Panel Missing ✅
**Status**: COMPLETED
**Priority**: P1 - CRITICAL GAMEPLAY

**Implementation**:
- Created full-featured CombatPanel component in `frontend-v2/src/components/combat/CombatPanel.ts`:
  - ✅ Shows/hides automatically based on `combat.is_active` state
  - ✅ Displays current round number
  - ✅ Displays current turn participant name
  - ✅ Full turn order list sorted by initiative (highest first)
  - ✅ Each participant shows: initiative value, name, [PLAYER] tag, HP (current/max)
  - ✅ Current turn participant highlighted with arrow, accent color, and glow effect
  - ✅ Filters out inactive participants
  - ✅ HP information pulled from character, monsters, and NPCs based on entity_type
- Added comprehensive CSS styling with BEM naming convention
  - Combat panel with danger-colored border
  - Turn order items with hover effects
  - Current turn highlighting with glow
  - Responsive layout
- Integrated into GameInterfaceScreen left panel (between Location and Chronicle)

**Files Modified**:
- Created: `frontend-v2/src/components/combat/CombatPanel.ts` - Full combat panel component
- Modified: `frontend-v2/src/screens/GameInterfaceScreen.ts` - Added combat panel integration
- Modified: `frontend-v2/styles/main.css` - Added combat panel CSS styles

**Validation**: TypeScript compiles without errors

---

#### Issue #7: Combat Suggestions Missing ✅
**Status**: COMPLETED
**Priority**: P1 - CRITICAL GAMEPLAY

**Implementation**:
- Created full-featured CombatSuggestionCard component in `frontend-v2/src/components/combat/CombatSuggestionCard.ts`:
  - ✅ Displays combat suggestions from allied NPCs during their turn
  - ✅ Shows NPC name as title ("{npc_name}'s Turn")
  - ✅ Displays suggested action text
  - ✅ "Use This Action" button (accept suggestion)
  - ✅ "Do Something Else" button (override suggestion)
  - ✅ Fail-fast validation of required fields
  - ✅ Disabled state during processing
  - ✅ Error handling with retry capability
- Added CombatSuggestion type to backend schema export
- Generated TypeScript types from backend (CombatSuggestion, AcceptCombatSuggestionRequest/Response)
- Updated SSE types to use proper CombatSuggestion interface
- Added `acceptCombatSuggestion()` method to GameApiService
- Integrated into GameInterfaceScreen:
  - ✅ Mounted in center panel above chat
  - ✅ Subscribed to `combat_suggestion` SSE events
  - ✅ Accept handler calls backend API endpoint
  - ✅ Override handler hides card and focuses chat input
  - ✅ System message feedback on override
- Added comprehensive CSS styling with BEM naming convention
  - Accent border, hover effects, disabled states
  - Responsive button styling
  - Proper spacing and layout

**Files Modified**:
- Created: `frontend-v2/src/components/combat/CombatSuggestionCard.ts`
- Modified: `app/api/routers/schemas.py` - Added CombatSuggestion export
- Generated: `frontend-v2/src/types/generated/CombatSuggestion.ts`
- Modified: `frontend-v2/src/types/sse.ts` - Updated CombatSuggestionEvent interface
- Modified: `frontend-v2/src/services/api/GameApiService.ts` - Added acceptCombatSuggestion method
- Modified: `frontend-v2/src/screens/GameInterfaceScreen.ts` - Integrated component and handlers
- Modified: `frontend-v2/styles/main.css` - Added combat suggestion card styles

**Validation**: TypeScript compiles without errors

---

## In Progress 🔨

### P1 Issues

**Combat suggestions completed! Moving to next P1 issue.**

---

## Pending P1 Issues 📋

### Issue #5: Chronicle Panel Severely Limited
**Priority**: P1 - CRITICAL GAMEPLAY
**Status**: NOT STARTED

**Missing Features**:
- Tabs: All / World / Locations / NPCs / My Notes
- Search box with clear button
- Location filter toggle
- Collapsible header
- Auto-generated memory entries (not just player journal)
- Entry metadata: location, NPCs, tags, timestamps

---

### Issue #13: Equipment Slots Not Interactive
**Priority**: P1 - CRITICAL GAMEPLAY
**Status**: NOT STARTED

**Required**:
- Click equipment slots to equip/unequip
- Item tooltips
- Interactive equipment management

---

### Issue #37: Item Slot Selector Missing
**Priority**: P1 - CRITICAL GAMEPLAY
**Status**: NOT STARTED

**Required**:
- Dropdown with valid slots for item type
- "Auto" option for automatic slot selection
- Slot compatibility validation
- Smart logic for two-handed weapons

---

## Summary Statistics

**Total P0 Issues**: 5
- ✅ Completed: 5 (Issues #1, #3, #4, #28, #29)
- 🔨 In Progress: 0
- 📋 Pending: 0

**Total P1 Issues**: 5
- ✅ Completed: 2 (Issues #6, #7)
- 🔨 In Progress: 0
- 📋 Pending: 3 (Issues #5, #13, #37)

**Overall Progress**: 7/10 critical issues resolved (70%)

---

## Next Steps

1. ✅ ~~Fix Issue #28: Add missing SSE event types and handlers~~ **COMPLETED**
2. ✅ ~~Fix Issue #29: Expand chat message type rendering~~ **COMPLETED**
3. ✅ ~~Fix Issue #6: Implement combat panel~~ **COMPLETED**
4. ✅ ~~Fix Issue #7: Implement combat suggestions~~ **COMPLETED**
5. **Fix Issue #5**: Enhance chronicle panel
6. **Fix Issue #13**: Equipment slots interactive functionality
7. **Fix Issue #37**: Item slot selector with validation

---

## Testing Notes

- All fixes validated with TypeScript compiler (`npm run type-check`)
- Runtime testing recommended for each completed issue
- Cross-reference with old frontend behavior for validation
