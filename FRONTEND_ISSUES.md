# Frontend-v2 Missing Features & Issues

**Status**: Frontend-v2 is currently a **significant downgrade** from the old frontend.
**Last Updated**: 2025-11-06 (Expanded investigation - 17 new issues found)

This document comprehensively lists ALL missing features, broken functionality, and discrepancies between the old frontend (`frontend/`) and the new TypeScript frontend (`frontend-v2/`).

**Total Issues**: 46 features analyzed (39 missing, 3 partial, 4 working)

---

## 🚨 Critical Missing Features

### 1. **No Way to Leave/Exit Game**
- **Old Frontend**: Header bar has "💾 Save" button (implies ability to exit)
- **Frontend-v2**: ❌ **NO WAY TO RETURN TO MAIN MENU/GAME LIST**
- **Impact**: Users are trapped in a game once started
- **Files**:
  - Old: `frontend/index.html:69`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

### 2. **Tool Calls Not Displayed in Chat**
- **Old Frontend**: Shows all tool calls with formatted parameters
  - Example: `🎲 roll_ability_check - STR DC 15`
  - Shows tool results: `📊 Ability Check Roll: 1d20+3 = 18 [15] (STR) - 🎯 SUCCESS!`
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Impact**: Players don't see what the AI is doing behind the scenes
- **Files**:
  - Old: `frontend/app.js:717-816` (SSE events `tool_call` and `tool_result`)
  - Missing from: `frontend-v2/src/components/chat/ChatPanel.ts`
  - Missing from: `frontend-v2/src/services/sse/SseService.ts`

### 3. **Party Member Selection Doesn't Work**
- **Old Frontend**: Clicking an NPC in party shows THEIR character sheet/inventory/equipment
  - Updates header: `"Elara Moonwhisper - Details"`
  - Calls `updateNPCSheet(npc)` to show NPC's stats
  - Shows NPC's equipment and inventory
- **Frontend-v2**: ❌ **ONLY EVER SHOWS PLAYER CHARACTER**
- **Impact**: Cannot view party member (NPC) details
- **Files**:
  - Old: `frontend/app.js:1182-1232` (`selectPartyMember`, `updateSelectedMemberDisplay`, `updateNPCSheet`)
  - Broken in: `frontend-v2/src/components/character-sheet/CharacterSheetPanel.ts` (hardcoded to `gameState.character`)
  - Broken in: `frontend-v2/src/components/inventory/InventoryPanel.ts` (hardcoded to `gameState.character`)

### 4. **Header Bar Completely Missing**
- **Old Frontend**: Full header bar with:
  - 📍 Current location + danger level indicator
  - 🕐 Game time (Day X, HH:MM)
  - ⚔️ Combat indicator (shows "COMBAT" when active)
  - 🤖 Active agent indicator (Narrative/Combat/Summarizer)
  - 💾 Save Game button
- **Frontend-v2**: ❌ **ENTIRE HEADER BAR MISSING**
- **Impact**: No context about location, time, combat status, or save functionality
- **Files**:
  - Old: `frontend/index.html:60-71`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

---

## 📋 Chronicle/Journal Panel Issues

### 5. **Chronicle Panel Severely Limited**
- **Old Frontend**: Rich chronicle system with:
  - **Tabs**: All / World / Locations / NPCs / My Notes
  - **Search box** with clear button
  - **Location filter** toggle ("Show all locations" checkbox)
  - **Collapsible** header (can collapse/expand entire panel)
  - Displays **BOTH**:
    - Auto-generated memory entries (world/location/NPC memories)
    - Player journal entries
  - Entry metadata: location, NPCs involved, tags, timestamps
- **Frontend-v2**: ❌ **BASIC IMPLEMENTATION ONLY**
  - Only shows player journal entries
  - NO filtering by type
  - NO search functionality
  - NO location filtering
  - NOT collapsible
  - Missing auto-generated memory entries
- **Impact**: Massive loss of world/story tracking functionality
- **Files**:
  - Old: `frontend/index.html:133-168`, `frontend/app.js:2942-3294`
  - Incomplete in: `frontend-v2/src/components/chronicle/ChroniclePanel.ts`

---

## 🎮 Combat & Game State Issues

### 6. **Combat Panel Missing**
- **Old Frontend**: Dedicated combat status panel showing:
  - Current round number
  - Current turn (character name)
  - Full turn order with initiative values
  - Automatically appears/disappears based on combat state
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Impact**: Players have no idea whose turn it is or combat status
- **Files**:
  - Old: `frontend/index.html:110-131`, `frontend/app.js:2406-2497`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

### 7. **Combat Suggestions Missing**
- **Old Frontend**: Shows combat suggestion card for ally turns:
  - Displays suggested action
  - "Use This Action" button
  - "Do Something Else" button
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Impact**: Combat for ally NPCs is broken
- **Files**:
  - Old: `frontend/index.html:482-494`, `frontend/app.js:1315-1443`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

### 8. **Location Time Display Missing**
- **Old Frontend**: Updates game time display from `gameState.game_time`
- **Frontend-v2**: ❌ **NO TIME DISPLAY**
- **Files**:
  - Old: `frontend/app.js:2358-2368`
  - Missing from: `frontend-v2/src/components/location/LocationPanel.ts`

### 9. **Danger Level Indicator Missing**
- **Old Frontend**: Shows danger level with color-coded indicators:
  - 🛡️ Safe (green)
  - ⚠️ Low/Moderate/High Danger (yellow/orange/red)
  - ☠️ EXTREME DANGER (red flashing)
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Files**:
  - Old: `frontend/app.js:2692-2729`
  - Missing from: `frontend-v2/src/components/location/LocationPanel.ts`

---

## 💬 Chat & Messaging Issues

### 10. **Markdown Rendering**
- **Old Frontend**: DM messages support full markdown:
  - **Bold**, *italic*, `code`
  - Lists (bulleted and numbered)
  - Escaped HTML for security
- **Frontend-v2**: ✅ **IMPLEMENTED**
  - Supports bold, italic, code, links
  - HTML escaping for security
  - Line breaks and paragraphs
  - May be missing list formatting
- **Status**: ✅ **WORKING** (with possible minor gaps)
- **Files**:
  - Old: `frontend/app.js:985-1006` (`parseMarkdown`)
  - Working in: `frontend-v2/src/utils/markdown.ts`, `frontend-v2/src/components/chat/ChatMessage.ts:38`

### 11. **NPC Dialogue Bubbles Missing**
- **Old Frontend**: Special rendering for NPC speech:
  - Shows speaker name
  - Different visual style
- **Frontend-v2**: ❌ **MISSING**
- **Files**:
  - Old: `frontend/app.js:1033-1051` (`addNpcDialogueBubble`)
  - Missing from: `frontend-v2/src/components/chat/ChatMessage.ts`

### 12. **Loading Indicators Missing**
- **Old Frontend**: Shows animated loading with rotating messages:
  - "Agent is thinking..."
  - "Rolling dice..."
  - "Consulting the rules..."
  - etc.
- **Frontend-v2**: ❌ **BASIC/MISSING**
- **Files**:
  - Old: `frontend/app.js:2843-2940`
  - Incomplete in: `frontend-v2/src/components/chat/LoadingIndicator.ts`

---

## 🎒 Inventory & Equipment Issues

### 13. **Equipment Slots Not Interactive**
- **Old Frontend**: Can click equipment slots to:
  - Equip items from inventory
  - Unequip to inventory
  - Shows item tooltips
- **Frontend-v2**: ❌ **DISPLAY ONLY, NO INTERACTION**
- **Impact**: Cannot manage equipment
- **Files**:
  - Old: `frontend/app.js:2092-2337` (interactive equipment management)
  - Display-only in: `frontend-v2/src/components/inventory/EquipmentSlots.ts`

### 14. **Inventory Missing Features**
- **Old Frontend**:
  - Shows item types/categories
  - Can equip items from inventory
  - Shows weight/capacity
- **Frontend-v2**: ❌ **BASIC LIST ONLY**
- **Files**:
  - Old: `frontend/app.js:2130-2337`
  - Incomplete in: `frontend-v2/src/components/inventory/ItemList.ts`

---

## 🎲 Character Sheet Issues

### 15. **Collapsible Sections Missing**
- **Old Frontend**: All major sections can collapse/expand:
  - Attacks
  - Abilities
  - Skills
  - Features
  - Racial Traits
  - Feats
  - Spellcasting
  - Equipment
  - Inventory
  - Chronicle
- **Frontend-v2**: ❌ **ALL SECTIONS ALWAYS EXPANDED**
- **Impact**: Overwhelming amount of information, poor UX
- **Files**:
  - Old: `frontend/index.html:234-463` (`.collapsible-header`)
  - Missing from: All character sheet components in `frontend-v2/src/components/character-sheet/`

### 16. **Attacks Display Missing**
- **Old Frontend**: Shows formatted attacks with:
  - Attack name
  - Attack bonus
  - Damage
  - Properties
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Files**:
  - Old: `frontend/index.html:234-242`, `frontend/app.js:1552-1592`
  - Missing from: `frontend-v2/src/components/character-sheet/`

### 17. **Conditions Display Missing**
- **Old Frontend**: Shows active conditions on character
- **Frontend-v2**: ❌ **COMPLETELY MISSING**
- **Files**:
  - Old: `frontend/index.html:465-471`, `frontend/app.js:2337-2357`
  - Missing from: `frontend-v2/src/components/character-sheet/`

### 18. **Spell Slots Visual Missing**
- **Old Frontend**: Visual grid showing used/available spell slots per level
- **Frontend-v2**: ❌ **TEXT ONLY**
- **Files**:
  - Old: `frontend/app.js:2028-2071`
  - Incomplete in: `frontend-v2/src/components/character-sheet/SpellsSection.ts`

---

## 👥 Party Panel Issues

### 19. **Party Member Cards Lack Detail**
- **Old Frontend**: Party cards show:
  - HP bar with percentage
  - AC, Level, Class
  - Active conditions
  - Status indicators (wounded, dead, etc.)
- **Frontend-v2**: ❌ **MINIMAL INFORMATION**
- **Files**:
  - Old: `frontend/app.js:1146-1180`
  - Incomplete in: `frontend-v2/src/components/party/PartyMemberCard.ts`

### 20. **Party Count Missing**
- **Old Frontend**: Shows "2/4" party size
- **Frontend-v2**: ❌ **MISSING**
- **Files**:
  - Old: `frontend/index.html:81`
  - Missing from: `frontend-v2/src/components/party/PartyPanel.ts`

---

## 🆕 New Game Flow Issues

### 21. **Content Pack Selection Missing**
- **Old Frontend**: Can select additional content packs when creating new game
- **Frontend-v2**: ❌ **MISSING FROM NEW GAME FLOW**
- **Files**:
  - Old: `frontend/index.html:44-50`, `frontend/app.js:450-542`
  - Missing from: `frontend-v2/src/screens/ScenarioSelectionScreen.ts`

### 22. **Saved Games Section Layout Different**
- **Old Frontend**: Clear separation with "Continue Your Adventures" vs "Start New Adventure"
- **Frontend-v2**: ✅ Has basic separation but different UX
- **Files**:
  - Old: `frontend/index.html:18-55`
  - Different in: `frontend-v2/src/screens/GameListScreen.ts`

---

## 📚 Catalog Browser Issues

### 23. **Catalog Browser Missing From Game**
- **Old Frontend**: Can access catalogs FROM within active game
- **Frontend-v2**: ❌ **ONLY FROM MAIN MENU**
- **Impact**: Cannot look up monsters/spells while playing
- **Files**:
  - Old: Button to open catalogs from game screen
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

### 24. **Catalog Navigation Different**
- **Old Frontend**: Tab-based navigation for catalog types
- **Frontend-v2**: ✅ Sidebar navigation (different but acceptable)

---

## 🐛 Other Issues

### 25. **Error Messages Missing**
- **Old Frontend**: `showError()` and `showNotification()` functions
- **Frontend-v2**: ❌ **NO CONSISTENT ERROR DISPLAY**
- **Files**:
  - Old: `frontend/app.js:2628-2650`
  - Incomplete in: `frontend-v2/src/services/state/StateStore.ts`

### 26. **Reconnection Logic**
- **Old Frontend**: Automatically reconnects SSE on disconnect with exponential backoff
- **Frontend-v2**: ✅ **IMPLEMENTED**
  - Exponential backoff reconnection (lines 219-236)
  - Max 5 reconnection attempts
  - Proper error handling
- **Status**: ✅ **WORKING**
- **Files**:
  - Old: `frontend/app.js:927-983`
  - Working in: `frontend-v2/src/services/sse/SseService.ts:219-236`

### 27. **Agent Indicator Missing**
- **Old Frontend**: Shows which agent is active (Narrative/Combat/Summarizer)
- **Frontend-v2**: ❌ **MISSING**
- **Files**:
  - Old: `frontend/index.html:66`, `frontend/app.js:2498-2519`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts`

---

## 🔌 SSE Event Handling Issues

### 28. **Missing SSE Event Types**
- **Old Frontend**: Handles 10+ SSE event types:
  - `connected` - Connection confirmation
  - `initial_narrative` - Opening scene for new games
  - `narrative` - DM narrative text (non-streaming)
  - `tool_call` - Tool invocation display
  - `tool_result` - Tool result display with formatted output
  - `npc_dialogue` - Special NPC speech rendering
  - `policy_warning` - Policy violation warnings
  - `combat_suggestion` - Allied NPC action suggestions
  - `scenario_info` - Full scenario data with locations
  - `game_update` - State updates
  - `complete` - Processing complete
  - `error` - Error events
- **Frontend-v2**: ❌ **ONLY HANDLES 7 EVENT TYPES**:
  - `narrative_chunk` (streaming)
  - `tool_call`
  - `game_update`
  - `combat_update`
  - `error`
  - `complete`
  - `thinking`
- **Missing Events**:
  - ❌ `initial_narrative` - New games won't show opening narrative
  - ❌ `tool_result` - No formatted tool results
  - ❌ `npc_dialogue` - No special NPC speech
  - ❌ `policy_warning` - No policy warnings
  - ❌ `combat_suggestion` - Combat suggestions won't display
  - ❌ `scenario_info` - Can't load full scenario data
  - ❌ `connected` - No connection confirmation
  - ❌ `narrative` (non-streaming) - May be replaced by `narrative_chunk`
- **Impact**: Critical gameplay features missing, poor error handling
- **Files**:
  - Old: `frontend/app.js:695-898`
  - Incomplete in: `frontend-v2/src/types/sse.ts:5-12`, `frontend-v2/src/services/sse/SseService.ts:142-156`

### 29. **Chat Message Types Limited**
- **Old Frontend**: Renders distinct message types:
  - `player` - User messages
  - `dm` - DM narrative
  - `system` - System messages
  - `tool` - Tool calls (blue with dice icon)
  - `tool-result` - Tool results (formatted)
  - `npc` - NPC dialogue (with speaker name)
  - `policy-warning` - Policy warnings (yellow)
  - `loading` - Loading states
  - `error` - Error messages (red)
  - `success` - Success notifications (green)
- **Frontend-v2**: ❌ **ONLY 3 MESSAGE TYPES**:
  - `user`, `assistant`, `system`
  - No tool calls, tool results, NPC dialogue, warnings, or status messages
- **Impact**: Players can't see tool calls, NPC dialogue, or warnings
- **Files**:
  - Old: `frontend/app.js:1009-1051` (message rendering with types)
  - Missing from: `frontend-v2/src/components/chat/ChatMessage.ts` (only handles 3 types)

---

## 💾 Save/Load Issues

### 30. **Conversation History Not Loaded on Resume**
- **Old Frontend**: When resuming a game:
  - Loads full conversation history from `gameState.conversation_history`
  - Detects and marks system messages (auto-combat, summaries)
  - Populates chat with all previous messages
  - Sets `skipInitialNarrative` flag to avoid duplicate opening
- **Frontend-v2**: ✅ **WORKING** - ChatPanel loads from `conversation_history`
- **Status**: **VERIFIED WORKING** in `ChatPanel.ts:78-79`
- **Files**:
  - Old: `frontend/app.js:346-377`
  - Working in: `frontend-v2/src/components/chat/ChatPanel.ts:78-79`

### 31. **Saved Game Time Display Missing**
- **Old Frontend**: Shows human-readable time since last save:
  - "X days ago" / "X hours ago" / "Recently"
  - Makes it easy to identify recent games
- **Frontend-v2**: ❌ **NO TIME DISPLAY**
- **Files**:
  - Old: `frontend/app.js:286-299`
  - Missing from: `frontend-v2/src/components/game/GameListItem.ts`

### 32. **Auto-Save Indicator Missing**
- **Old Frontend**: Shows "💾 Auto-saved" briefly after sending message
- **Frontend-v2**: ❌ **NO AUTO-SAVE FEEDBACK**
- **Files**:
  - Old: `frontend/app.js:972-976`
  - Missing from: `frontend-v2/src/components/chat/ChatPanel.ts`

### 33. **Save Button Time Update Missing**
- **Old Frontend**: Manual save shows "✅ Saved at HH:MM" for 3 seconds
- **Frontend-v2**: ❌ **NO VISUAL FEEDBACK FOR MANUAL SAVE** (and no save button)
- **Files**:
  - Old: `frontend/app.js:2607-2616`
  - Missing from: `frontend-v2/src/screens/GameInterfaceScreen.ts` (no save button exists)

---

## ⌨️ UX/Interaction Issues

### 34. **Keyboard Shortcuts**
- **Old Frontend**:
  - **Enter**: Send message
  - **Shift+Enter**: New line in textarea
- **Frontend-v2**: ✅ **IMPLEMENTED** in `ChatInput.ts`
- **Status**: ✅ **WORKING**

### 35. **Input State Management Missing**
- **Old Frontend**: During AI processing:
  - Disables input and send button ✓
  - Changes placeholder to "Waiting for agent response..."
  - Changes send button text to "Agent is thinking..."
  - Auto-focuses input after response
  - Adds loading animation to agent indicator
- **Frontend-v2**: ❌ **PARTIAL IMPLEMENTATION**
  - Input is disabled (✓)
  - Placeholder NOT changed
  - Button text NOT changed
  - Auto-focus after response (✓ - line 158)
  - No agent indicator animation
- **Impact**: Less clear feedback during processing
- **Files**:
  - Old: `frontend/app.js:2843-2896`
  - Incomplete in: `frontend-v2/src/components/chat/ChatPanel.ts:140-159`

### 36. **Spell Name Resolution Missing**
- **Old Frontend**: Fetches spell display names via `/api/catalogs/resolve-names` endpoint
  - Stores in `window.spellNameMappings`
  - Shows proper spell names instead of indexes
- **Frontend-v2**: ❌ **SHOWS SPELL INDEXES ONLY**
- **Files**:
  - Old: `frontend/app.js:658-674`
  - Missing from: `frontend-v2/src/components/character-sheet/SpellsSection.ts`

---

## 🎒 Additional Inventory Issues

### 37. **Item Slot Selector Missing**
- **Old Frontend**: When equipping items:
  - Shows dropdown with valid slots for item type
  - "Auto" option for automatic slot selection
  - Validates slot compatibility (e.g., shields can go in main_hand or off_hand)
  - Smart logic for two-handed weapons
- **Frontend-v2**: ❌ **NO SLOT SELECTION**
- **Impact**: Cannot equip items to specific slots
- **Files**:
  - Old: `frontend/app.js:2179-2201`, `frontend/app.js:2222-2254` (valid slots logic)
  - Missing from: `frontend-v2/src/components/inventory/ItemList.ts`

### 38. **Equipment Status Display Missing**
- **Old Frontend**: In inventory, equipped items show:
  - "Equipped (Main Hand)" or similar
  - Shows which slot(s) the item occupies
  - Grayed out or marked as equipped
- **Frontend-v2**: ❌ **NO EQUIPPED STATUS IN INVENTORY**
- **Files**:
  - Old: `frontend/app.js:2202-2215`
  - Missing from: `frontend-v2/src/components/inventory/ItemList.ts`

---

## 📜 Additional Chronicle Issues

### 39. **Chronicle Location Names Missing**
- **Old Frontend**: Resolves location IDs to human-readable names
  - Uses `window.currentScenario.locations` to look up names
  - Shows "Goblin Cave" instead of "location_001"
- **Frontend-v2**: ❌ **SHOWS RAW LOCATION IDs**
- **Files**:
  - Old: `frontend/app.js:3246-3254`
  - Missing from: `frontend-v2/src/components/chronicle/ChronicleEntry.ts`

### 40. **Chronicle In-Game Time Missing**
- **Old Frontend**: Chronicle timestamps use in-game time:
  - "Day 3, Hour 14" instead of real-world timestamp
  - Uses `gameState.time_state` when available
- **Frontend-v2**: ❌ **SHOWS REAL-WORLD TIMESTAMPS**
- **Files**:
  - Old: `frontend/app.js:3235-3244`
  - Missing from: `frontend-v2/src/components/chronicle/ChronicleEntry.ts`

---

## 🎮 Additional Game Selection Issues

### 41. **Auto-Selection Missing**
- **Old Frontend**:
  - Auto-selects first scenario card on load
  - Shows content pack section after scenario selected
- **Frontend-v2**: ❌ **NO AUTO-SELECTION**
- **Files**:
  - Old: `frontend/app.js:413-418`
  - Missing from: `frontend-v2/src/screens/ScenarioSelectionScreen.ts`

### 42. **Start Button Conditional Enable Missing**
- **Old Frontend**: Start button only enabled when BOTH:
  - Character is selected
  - Scenario is selected
- **Frontend-v2**: ❌ **ENABLE LOGIC UNCLEAR**
- **Files**:
  - Old: `frontend/app.js:443`, `frontend/app.js:559`
  - Needs verification in: `frontend-v2/src/screens/ScenarioSelectionScreen.ts`

### 43. **Catalog Pack Filtering Missing**
- **Old Frontend**: In catalog browser:
  - Shows checkboxes for each content pack
  - Filters catalog items by selected packs
  - Resets to page 1 when filter changes
- **Frontend-v2**: ❌ **NO PACK FILTERING**
- **Impact**: Cannot filter catalogs by content pack
- **Files**:
  - Old: `frontend/app.js:1723-1764`
  - Missing from: `frontend-v2/src/components/catalog/ContentPackFilter.ts`

### 44. **Catalog Pagination Missing**
- **Old Frontend**: Full pagination system in catalog browser:
  - Page numbers with prev/next buttons
  - Configurable items per page (default 20)
  - Page indicator (e.g., "Page 2 of 15")
  - Efficient handling of large catalogs (100+ items)
- **Frontend-v2**: ❌ **NO PAGINATION**
  - Loads ALL items at once
  - Performance issue for large catalogs
  - No way to navigate through pages
- **Impact**: Poor performance with large catalogs, poor UX
- **Files**:
  - Old: `frontend/app.js:1634-1713`, `frontend/app.js:1771-1939` (pagination rendering & logic)
  - Missing from: `frontend-v2/src/screens/CatalogBrowserScreen.ts` (loads all items at once)

---

## 📊 Summary Statistics

| Category | Missing Features | Partial Implementation | Working |
|----------|------------------|------------------------|---------|
| **Critical UX** | 4 | 0 | 0 |
| **Chronicle/Journal** | 3 | 0 | 0 |
| **Combat** | 3 | 0 | 0 |
| **Chat/Messaging** | 4 | 1 | 0 |
| **SSE Events** | 2 | 0 | 0 |
| **Inventory/Equipment** | 4 | 0 | 0 |
| **Character Sheet** | 4 | 0 | 0 |
| **Party Management** | 2 | 0 | 0 |
| **Game Flow** | 4 | 1 | 0 |
| **Save/Load** | 3 | 0 | 1 |
| **UX/Interaction** | 2 | 1 | 1 |
| **Catalog** | 2 | 0 | 0 |
| **Other** | 2 | 0 | 2 |
| **TOTAL** | **39** | **3** | **4** |

**Overall Assessment**: Frontend-v2 is missing approximately **85% of old frontend features** (39 missing out of 46 total features analyzed).

**New Issues Found**: 17 additional issues discovered in this investigation (issues #28-44).

---

## 🔥 Prioritized Fix List (P0 = Highest Priority)

### **P0 - Blocking Issues** (Game is unusable without these)
1. ❌ Exit/Leave Game button (#1)
2. ❌ Party member selection (showing NPC details) (#3)
3. ❌ Header bar (location, time, save button) (#4)
4. ❌ SSE event types missing (tool_result, npc_dialogue, combat_suggestion, initial_narrative) (#28)
5. ❌ Chat message types limited (no tool/tool-result/npc rendering) (#29)

### **P1 - Critical Gameplay** (Severely impacts gameplay)
6. ❌ Combat panel (#6)
7. ❌ Combat suggestions (#7)
8. ❌ Chronicle filtering and search (#5)
9. ❌ Equipment interaction (equip/unequip) (#13)
10. ❌ Item slot selector (#37)

### **P2 - Important UX** (Significant UX degradation)
11. ❌ Collapsible sections (#15)
12. ✅ Markdown rendering (#10) - **ACTUALLY WORKING**
13. ❌ NPC dialogue bubbles (#11)
14. ❌ Danger level indicators (#9)
15. ❌ Attacks display (#16)
16. ❌ Conditions display (#17)
17. ❌ Party member details (#19)
18. ❌ Equipment status display in inventory (#38)
19. ❌ Input state management (placeholder/button text updates) (#35)

### **P3 - Nice to Have** (Quality of life)
20. ❌ Content pack selection in new game flow (#21)
21. ❌ Catalog access from game (#23)
22. ❌ Catalog pack filtering (#43)
23. ❌ Catalog pagination (#44)
24. ❌ Loading message rotation (#12)
25. ❌ Party count display (#20)
26. ❌ Spell slot visualization (#18)
27. ❌ Spell name resolution (#36)
28. ❌ Chronicle location names (#39)
29. ❌ Chronicle in-game time (#40)
30. ❌ Saved game time display (#31)
31. ❌ Auto-save indicator (#32)
32. ❌ Save button time update (#33)
33. ❌ Auto-selection of scenario (#41)
34. ❌ Start button conditional enable (#42)

---

## 🎯 Recommended Approach

1. **First**: Fix P0 issues to make frontend-v2 usable at all
   - Focus on SSE event handling (#28, #29) and header bar (#4)
   - Exit game functionality (#1) and party member selection (#3)
2. **Then**: Implement P1 features to restore core gameplay
   - Combat system (#6, #7) and equipment management (#13, #37)
   - Chronicle filtering (#5)
3. **Finally**: Add P2/P3 features for full parity
   - UI polish and quality-of-life improvements
   - Visual enhancements and time-saving features

**Estimated effort**: 60-80 hours of development to achieve full feature parity (increased from 40-60 due to additional issues found).

**Key Architecture Notes**:
- SSE event system needs extension to handle 8+ additional event types
- Chat message rendering needs refactor to support 10 message types (not just 3)
- Backend types are source of truth - use generated types
- Follow SOLID, DRY, fail-fast principles
- All fixes should use existing backend schemas and API endpoints
