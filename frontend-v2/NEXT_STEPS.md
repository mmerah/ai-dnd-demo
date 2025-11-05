# Frontend MVP Completion Plan

## Overview
Complete the frontend refactor to reach feature parity with the original frontend, following SOLID, KISS, DRY, clean architecture, and fail-fast principles.

**Current Status**: Phase 4 complete - Core 3-panel game interface working
**Target**: Full feature parity with original frontend, minimal but effective testing

---

## Phases Overview

- **Phase 5**: Additional Screens & Navigation (Game List, Character Selection, Scenario Selection)
- **Phase 6**: Extended Components (Chronicle CRUD, Tool Call Display, Character Sheet, Inventory)
- **Phase 7**: Catalog Browser & Content Packs
- **Phase 8**: Testing (Services + Critical Paths)

---

## Phase 5: Additional Screens & Navigation

**Goal**: Implement screen flow: Landing → Game List → Character/Scenario Selection → Game Interface

### 5.1: Game List Screen
**Purpose**: Browse and load existing saved games

**Files to Create**:
```
src/screens/GameListScreen.ts          (~150 lines)
src/components/game/GameListItem.ts    (~80 lines)
```

**Features**:
- Fetch list of saved games from `/api/game/list`
- Display game cards with: scenario name, character name, last saved date, created date
- Click to load game → navigate to GameInterfaceScreen
- "New Game" button → navigate to CharacterSelectionScreen
- Delete game functionality
- Loading states and error handling
- Empty state ("No saved games")

**API Integration**:
- `GET /api/game/list` - Already exists in GameApiService ✅
- `DELETE /api/game/{id}` - Already exists in GameApiService ✅

**Component Structure**:
```
GameListScreen
  ├── Header ("Saved Games" + "New Game" button)
  ├── Loading indicator (if fetching)
  ├── Error display (if fetch failed)
  ├── Game list (map of GameListItem)
  └── Empty state (if no games)

GameListItem (card)
  ├── Scenario name
  ├── Character name
  ├── Timestamps (last saved, created)
  ├── Load button
  └── Delete button (with confirmation)
```

**CSS**:
- Add `.game-list-screen` styles to main.css (~50 lines)
- Grid layout for game cards
- Hover effects, card styling

**Testing**:
- Unit test: GameApiService.listGames()
- Unit test: GameApiService.deleteGame()

---

### 5.2: Character Selection Screen
**Purpose**: Select a pre-made character to start a new game

**Files to Create**:
```
src/screens/CharacterSelectionScreen.ts    (~120 lines)
src/components/character/CharacterCard.ts  (~100 lines)
src/services/api/CatalogApiService.ts      (~80 lines)
```

**Features**:
- Fetch available characters from `/api/characters`
- Display character cards with: name, race, class, level, portrait (if available)
- Click to select character
- "Back" button → return to GameListScreen
- "Next" button → proceed to ScenarioSelectionScreen (disabled until selection)
- Loading states and error handling

**API Integration**:
- `GET /api/characters` - Need to create CatalogApiService
- Store selected character ID in state

**Component Structure**:
```
CharacterSelectionScreen
  ├── Header ("Select Your Character")
  ├── Loading indicator
  ├── Character grid (map of CharacterCard)
  ├── Navigation buttons (Back, Next)
  └── Error display

CharacterCard (selectable card)
  ├── Character portrait (placeholder if none)
  ├── Name
  ├── Race + Class
  ├── Level
  └── Selected state (border highlight)
```

**State Management**:
- Add to StateStore: `selectedCharacterId`, `selectedScenarioId`
- Track selection flow state

**CSS**:
- Add `.character-selection-screen` styles (~60 lines)
- Grid layout for character cards
- Selection highlighting

---

### 5.3: Scenario Selection Screen
**Purpose**: Select a scenario to start a new game

**Files to Create**:
```
src/screens/ScenarioSelectionScreen.ts    (~130 lines)
src/components/scenario/ScenarioCard.ts   (~110 lines)
```

**Features**:
- Fetch available scenarios from `/api/scenarios`
- Display scenario cards with: name, description, difficulty (if available)
- Click to select scenario
- "Back" button → return to CharacterSelectionScreen
- "Start Game" button → create game and navigate to GameInterfaceScreen
- Loading states and error handling
- Show confirmation before starting game

**API Integration**:
- `GET /api/scenarios` - Need to add to CatalogApiService
- `POST /api/game/new` - Already exists in GameApiService ✅

**Component Structure**:
```
ScenarioSelectionScreen
  ├── Header ("Select Your Scenario")
  ├── Loading indicator
  ├── Scenario grid (map of ScenarioCard)
  ├── Navigation buttons (Back, Start Game)
  └── Error display

ScenarioCard (selectable card)
  ├── Scenario title
  ├── Description preview
  ├── Difficulty badge (if available)
  └── Selected state (border highlight)
```

**Workflow**:
1. User selects scenario
2. Clicks "Start Game"
3. Call `POST /api/game/new` with character_id + scenario_id
4. Receive game_id
5. Navigate to GameInterfaceScreen with game_id

**CSS**:
- Add `.scenario-selection-screen` styles (~60 lines)
- Grid layout for scenario cards
- Difficulty badge styling

---

### 5.4: Screen Navigation & Routing
**Purpose**: Wire up navigation between all screens

**Files to Create/Update**:
```
src/screens/ScreenManager.ts              (~150 lines)
src/main.ts                                (update ~30 lines)
```

**Features**:
- Simple routing system (no external router library - KISS principle)
- URL hash-based routing: `#/game-list`, `#/character-select`, `#/scenario-select`, `#/game/{id}`
- Navigation methods: `navigateTo(route, params?)`
- Back button support (browser history)
- Current screen state management
- Screen transitions with cleanup

**ScreenManager Structure**:
```typescript
class ScreenManager {
  private currentScreen: Screen | null = null;
  private container: HTMLElement;

  navigateTo(route: string, params?: object): void;
  goBack(): void;
  getCurrentRoute(): string;
  private mountScreen(screen: Screen): void;
  private unmountCurrentScreen(): void;
}
```

**Routes**:
- `/` or `#/` → GameListScreen
- `#/character-select` → CharacterSelectionScreen
- `#/scenario-select` → ScenarioSelectionScreen
- `#/game/:gameId` → GameInterfaceScreen

**Main.ts Updates**:
- Initialize ScreenManager instead of directly mounting GameInterfaceScreen
- Parse initial route from URL
- Set up window.onhashchange listener

**Testing**:
- Manual navigation testing (all routes work)
- Browser back button works
- Screen cleanup verified (no memory leaks)

---

### Phase 5 Summary
**Files Created**: 8 files
**Lines of Code**: ~930 lines TypeScript + ~170 lines CSS
**Dependencies**: None (vanilla routing)
**Definition of Done**:
- ✅ Can browse and load saved games
- ✅ Can select character from available list
- ✅ Can select scenario from available list
- ✅ Can create new game and enter game interface
- ✅ Navigation works (forward, back, URL updates)
- ✅ All screens have loading and error states
- ✅ TypeScript strict mode passing, zero `any` types

---

## Phase 6: Extended Components

**Goal**: Add Chronicle CRUD, Tool Call Display, Character Sheet Panel, Inventory Panel

### 6.1: Chronicle Panel with CRUD
**Purpose**: Display, filter, search, and manage chronicle/journal entries

**Files to Create**:
```
src/components/chronicle/ChroniclePanel.ts       (~180 lines)
src/components/chronicle/ChronicleEntry.ts       (~90 lines)
src/components/chronicle/ChronicleFilters.ts     (~100 lines)
src/components/chronicle/JournalEntryModal.ts    (~120 lines)
src/services/api/JournalApiService.ts            (~100 lines)
```

**Features**:
- Display all chronicle entries from game state
- **Filtering**:
  - By category: Event, NPC, Location, Quest, Item
  - By location
  - Date range
- **Search**: Text search across title and content
- **CRUD Operations**:
  - Create: "Add Entry" button → modal
  - Read: Display entries in chronological order
  - Update: Click entry → edit modal
  - Delete: Delete button with confirmation
- Collapsible/expandable section in left panel
- Pagination or infinite scroll for long lists

**API Integration**:
- `GET /api/game/{id}/chronicle` - Fetch all entries (if separate endpoint exists)
- `POST /api/game/{id}/journal` - Create entry
- `PUT /api/game/{id}/journal/{entry_id}` - Update entry
- `DELETE /api/game/{id}/journal/{entry_id}` - Delete entry

**Component Structure**:
```
ChroniclePanel
  ├── Header ("Chronicle" + filters toggle + "Add Entry" button)
  ├── ChronicleFilters (collapsible)
  │   ├── Category filter (dropdown)
  │   ├── Location filter (dropdown)
  │   ├── Search input
  │   └── Clear filters button
  ├── Entry list (filtered/searched)
  │   └── ChronicleEntry[] (map)
  └── Empty state

ChronicleEntry (card)
  ├── Category badge
  ├── Title
  ├── Content preview (truncated)
  ├── Location badge (if present)
  ├── Timestamp
  ├── Edit button
  └── Delete button

JournalEntryModal (overlay)
  ├── Close button
  ├── Title input
  ├── Category dropdown
  ├── Content textarea
  ├── Location dropdown (optional)
  ├── Cancel button
  └── Save button
```

**State Management**:
- Chronicle entries are part of GameState
- After CRUD operations, reload game state to get updated entries
- Optimistic updates for better UX

**CSS**:
- Add `.chronicle-panel` styles (~80 lines)
- Modal overlay styles
- Filter controls
- Entry card styling

**Testing**:
- Unit test: JournalApiService CRUD methods
- Integration test: Create → list → update → delete flow

---

### 6.2: Tool Call Display
**Purpose**: Show AI tool calls as they happen in the chat

**Files to Update**:
```
src/components/chat/ChatPanel.ts           (update ~30 lines)
src/components/chat/ToolCallMessage.ts     (create ~80 lines)
```

**Features**:
- Subscribe to `tool_call` SSE events
- Display tool calls in chat feed with special styling
- Show: tool name, arguments (formatted JSON), result (if available)
- Collapsible/expandable for large arguments
- Different styling from regular messages

**Component Structure**:
```
ToolCallMessage
  ├── Tool icon/badge
  ├── Tool name
  ├── Arguments (collapsible JSON)
  ├── Result (collapsible, if present)
  └── Timestamp
```

**SSE Integration**:
- Already have SSE service ✅
- Add handler in GameInterfaceScreen for `tool_call` events
- Append ToolCallMessage to chat history (separate from conversation)

**CSS**:
- Add `.tool-call-message` styles (~40 lines)
- Different background color (e.g., dark blue)
- Monospace font for JSON
- Expand/collapse icons

**Testing**:
- Manual test: Verify tool calls appear in chat during AI actions

---

### 6.3: Character Sheet Expandable Panel
**Purpose**: Show full character details when selected in party

**Files to Create**:
```
src/components/character/CharacterSheetPanel.ts    (~200 lines)
src/components/character/AbilitiesSection.ts       (~80 lines)
src/components/character/SkillsSection.ts          (~90 lines)
src/components/character/FeaturesSection.ts        (~70 lines)
src/components/character/SpellsSection.ts          (~100 lines)
```

**Features**:
- Replaces PartyPanel when "View Full Sheet" button clicked
- Shows complete character information:
  - Basic info (name, race, class, level, XP)
  - Abilities (STR, DEX, CON, INT, WIS, CHA) with modifiers
  - Skills (all skills with bonuses)
  - Saving throws
  - Combat stats (HP, AC, Initiative, Speed)
  - Conditions
  - Features & Traits
  - Spells (if spellcaster)
  - Proficiencies
- "Back to Party" button to return to PartyPanel
- Tabbed or sectioned layout for organization

**Component Structure**:
```
CharacterSheetPanel
  ├── Header ("Character Sheet" + "Back to Party" button)
  ├── Basic Info Section
  ├── AbilitiesSection (6 ability scores + modifiers)
  ├── SkillsSection (all skills in grid)
  ├── Combat Stats Section
  ├── Conditions Section
  ├── FeaturesSection (expandable list)
  └── SpellsSection (if applicable)
```

**State Management**:
- Add `showCharacterSheet: boolean` to StateStore
- When true, show CharacterSheetPanel instead of PartyPanel in right panel
- Character data comes from GameState (already have it)

**CSS**:
- Add `.character-sheet-panel` styles (~100 lines)
- Grid layouts for abilities/skills
- Tabbed interface styling (if using tabs)

**Testing**:
- Manual test: Verify all character data displays correctly
- Test toggle between PartyPanel and CharacterSheetPanel

---

### 6.4: Inventory Expandable Panel
**Purpose**: Show full inventory with equipment slots

**Files to Create**:
```
src/components/inventory/InventoryPanel.ts        (~180 lines)
src/components/inventory/EquipmentSlots.ts        (~100 lines)
src/components/inventory/ItemList.ts              (~80 lines)
src/components/inventory/CurrencyDisplay.ts       (~50 lines)
```

**Features**:
- Replaces PartyPanel when "View Inventory" button clicked
- Shows:
  - Currency (GP, SP, CP)
  - Equipment slots (weapon, armor, shield, rings, etc.)
  - Backpack items (sorted/filtered)
  - Item details on hover/click
  - Weight carried / capacity
- "Back to Party" button
- Filter by item type (weapon, armor, consumable, etc.)
- Search by name

**Component Structure**:
```
InventoryPanel
  ├── Header ("Inventory" + "Back to Party" button)
  ├── CurrencyDisplay
  ├── EquipmentSlots
  │   ├── Weapon slot
  │   ├── Armor slot
  │   ├── Shield slot
  │   └── Other slots...
  ├── Backpack
  │   ├── Filter/Search controls
  │   ├── Weight display
  │   └── ItemList (grid of items)
  └── Item detail tooltip/panel
```

**State Management**:
- Add `showInventory: boolean` to StateStore
- Inventory data from GameState (character.inventory, character.equipment)
- Read-only for MVP (no drag-drop, no equip/unequip actions)

**CSS**:
- Add `.inventory-panel` styles (~80 lines)
- Equipment slots grid
- Item card styling
- Currency display

**Testing**:
- Manual test: Verify inventory displays correctly
- Test toggle between PartyPanel and InventoryPanel

---

### 6.5: Right Panel Toggle System
**Purpose**: Manage switching between Party, Character Sheet, and Inventory panels

**Files to Update**:
```
src/screens/GameInterfaceScreen.ts         (update ~50 lines)
src/services/state/StateStore.ts           (update ~30 lines)
src/components/party/PartyPanel.ts         (add buttons ~20 lines)
```

**Features**:
- PartyPanel gets two new buttons:
  - "View Character Sheet" (on selected member)
  - "View Inventory" (on selected member)
- StateStore tracks `rightPanelView: 'party' | 'character-sheet' | 'inventory'`
- GameInterfaceScreen conditionally renders correct panel
- Each panel has "Back to Party" button

**State Management**:
```typescript
// Add to StateStore
private rightPanelView = new Observable<'party' | 'character-sheet' | 'inventory'>('party');

setRightPanelView(view: 'party' | 'character-sheet' | 'inventory'): void;
getRightPanelView(): string;
onRightPanelViewChange(callback): Unsubscribe;
```

**GameInterfaceScreen Logic**:
```typescript
// In render(), right panel:
switch (rightPanelView) {
  case 'party':
    mount PartyPanel
  case 'character-sheet':
    mount CharacterSheetPanel
  case 'inventory':
    mount InventoryPanel
}
```

---

### Phase 6 Summary
**Files Created**: 15 files
**Lines of Code**: ~1,600 lines TypeScript + ~300 lines CSS
**Dependencies**: None
**Definition of Done**:
- ✅ Chronicle panel shows all entries with filtering and search
- ✅ Can create, edit, delete journal entries
- ✅ Tool calls display in chat as they happen
- ✅ Can view full character sheet in right panel
- ✅ Can view full inventory in right panel
- ✅ Can toggle between party/character/inventory views
- ✅ TypeScript strict mode passing, zero `any` types

---

## Phase 7: Catalog Browser & Content Packs

**Goal**: Browse reference data (spells, items, monsters) with content pack filtering

### 7.1: Catalog Browser Screen
**Purpose**: Browse all reference data from the catalog

**Files to Create**:
```
src/screens/CatalogBrowserScreen.ts            (~150 lines)
src/components/catalog/CatalogSidebar.ts       (~100 lines)
src/components/catalog/CatalogItemList.ts      (~120 lines)
src/components/catalog/CatalogItemDetail.ts    (~130 lines)
src/components/catalog/ContentPackFilter.ts    (~80 lines)
```

**Features**:
- Access from GameInterfaceScreen (button in header or menu)
- Two-panel layout:
  - Left: Category sidebar + content pack filter
  - Right: Item list + detail view
- Categories:
  - Spells
  - Items (equipment, magic items)
  - Monsters
  - Races
  - Classes
  - Backgrounds
  - Feats
- Content pack filtering (same as old frontend)
- Search within category
- Detail view shows full item information

**API Integration**:
- `GET /api/catalogs/spells` - Already exists ✅
- `GET /api/catalogs/items` - Already exists ✅
- `GET /api/catalogs/monsters` - Already exists ✅
- `GET /api/content-packs` - Already exists ✅
- Similar endpoints for other categories

**Component Structure**:
```
CatalogBrowserScreen
  ├── Header ("Catalog Browser" + "Back to Game" button)
  ├── CatalogSidebar (left)
  │   ├── Category list (selectable)
  │   └── ContentPackFilter
  │       ├── "All Content Packs" option
  │       └── Content pack checkboxes
  └── Main area (right)
      ├── CatalogItemList (grid or list)
      │   ├── Search input
      │   └── Item cards (map)
      └── CatalogItemDetail (expandable/modal)
          └── Full item details
```

**State Management**:
- Selected category
- Selected content packs (array of IDs)
- Search query
- Selected item for detail view

**CSS**:
- Add `.catalog-browser-screen` styles (~120 lines)
- Two-panel layout (20% | 80%)
- Sidebar styling
- Item grid/list styling
- Detail panel styling

**Testing**:
- Unit test: CatalogApiService methods
- Manual test: Browse all categories, filter by content pack, search

---

### 7.2: Content Pack Filtering Logic
**Purpose**: Filter catalog items by selected content packs

**Files to Create**:
```
src/utils/catalogFilters.ts    (~60 lines)
```

**Features**:
- Pure functions for filtering items by content pack
- Combine with text search
- Handle "All Content Packs" case
- Type-safe filtering

**Functions**:
```typescript
function filterByContentPacks<T extends { content_pack?: string }>(
  items: T[],
  selectedPacks: string[]
): T[];

function filterBySearch<T>(
  items: T[],
  searchQuery: string,
  searchFields: (keyof T)[]
): T[];

function combineFilters<T>(
  items: T[],
  filters: Array<(item: T) => boolean>
): T[];
```

**Testing**:
- Unit tests for all filter functions
- Edge cases: empty selection, "All", no matches

---

### 7.3: Catalog Screen Integration
**Purpose**: Add navigation to catalog from game interface

**Files to Update**:
```
src/screens/GameInterfaceScreen.ts    (add button ~20 lines)
src/screens/ScreenManager.ts          (add route ~10 lines)
```

**Features**:
- "Browse Catalog" button in game interface header
- Opens CatalogBrowserScreen
- "Back to Game" returns to GameInterfaceScreen
- Game state persists while browsing catalog

**Navigation**:
- Route: `#/game/:gameId/catalog`
- From game: `navigateTo('/game/{id}/catalog')`
- Back: `navigateTo('/game/{id}')`

---

### Phase 7 Summary
**Files Created**: 6 files
**Lines of Code**: ~760 lines TypeScript + ~120 lines CSS
**Dependencies**: None
**Definition of Done**:
- ✅ Can browse all catalog categories
- ✅ Can filter by content pack (exact same behavior as old frontend)
- ✅ Can search within category
- ✅ Can view full details of any catalog item
- ✅ Navigation works (to/from game interface)
- ✅ TypeScript strict mode passing, zero `any` types

---

## Phase 8: Testing

**Goal**: Add minimal but effective tests for critical paths

### 8.1: Service Unit Tests
**Purpose**: Test all API services and state management

**Files to Create**:
```
src/services/api/__tests__/ApiService.test.ts          (~120 lines)
src/services/api/__tests__/GameApiService.test.ts      (~150 lines)
src/services/api/__tests__/CatalogApiService.test.ts   (~100 lines)
src/services/api/__tests__/JournalApiService.test.ts   (~100 lines)
src/services/state/__tests__/Observable.test.ts        (~100 lines)
src/services/state/__tests__/StateStore.test.ts        (~150 lines)
src/services/sse/__tests__/SseService.test.ts          (~120 lines)
```

**Test Coverage**:
- **ApiService**:
  - GET/POST/PUT/DELETE methods
  - Error handling (4xx, 5xx, network errors)
  - Timeout handling
  - Request/response format
- **GameApiService**:
  - All game-related endpoints
  - createGame, getGameState, sendAction
  - listGames, deleteGame
- **CatalogApiService**:
  - All catalog endpoints
  - Content pack fetching
- **JournalApiService**:
  - CRUD operations
- **Observable**:
  - subscribe/unsubscribe
  - notify on change
  - immediate subscription
- **StateStore**:
  - All getters/setters
  - Validation logic
  - Observer notifications
- **SseService**:
  - Connection/disconnection
  - Event routing
  - Reconnect logic
  - Error handling

**Mocking Strategy**:
- Use Vitest's built-in mocking
- Mock `fetch` globally for API tests
- Mock `EventSource` for SSE tests
- Use test fixtures for API responses

**Example Test Structure**:
```typescript
// ApiService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiService } from '../ApiService';

describe('ApiService', () => {
  let apiService: ApiService;

  beforeEach(() => {
    apiService = new ApiService('http://test.api');
    global.fetch = vi.fn();
  });

  describe('get', () => {
    it('should make GET request with correct URL', async () => {
      const mockResponse = { data: 'test' };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.get('/endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://test.api/endpoint',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw ApiError on 4xx response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(apiService.get('/endpoint')).rejects.toThrow('HTTP 404');
    });
  });

  // More tests...
});
```

**Commands**:
```bash
npm run test                    # Run all tests
npm run test:coverage           # Run with coverage report
npm run test:watch              # Watch mode
```

**Coverage Target**:
- Services: 80%+ coverage
- Focus on critical paths and error handling
- Don't test trivial getters/setters unless they have logic

---

### 8.2: Component Integration Tests
**Purpose**: Test critical component interactions (minimal, essential only)

**Files to Create**:
```
src/components/chat/__tests__/ChatPanel.test.ts       (~100 lines)
src/components/party/__tests__/PartyPanel.test.ts     (~80 lines)
```

**Test Coverage** (minimal):
- **ChatPanel**:
  - Renders messages from state
  - Sends message on submit
  - Shows loading indicator when processing
  - Disables input when processing
- **PartyPanel**:
  - Renders party members
  - Handles member selection
  - Updates on state change

**Mocking Strategy**:
- Mock StateStore
- Mock onSendMessage callback
- Use JSDOM for DOM operations

**Example**:
```typescript
describe('ChatPanel', () => {
  let mockStateStore: StateStore;
  let mockOnSendMessage: vi.Mock;
  let container: HTMLElement;

  beforeEach(() => {
    mockStateStore = createMockStateStore();
    mockOnSendMessage = vi.fn();
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    container.remove();
  });

  it('should render messages from game state', () => {
    const chatPanel = new ChatPanel({
      stateStore: mockStateStore,
      onSendMessage: mockOnSendMessage,
    });
    chatPanel.mount(container);

    const messages = container.querySelectorAll('.chat-message');
    expect(messages.length).toBe(mockStateStore.getGameState()!.conversation_history.length);
  });
});
```

**Coverage Target**:
- Critical components only: ChatPanel, PartyPanel
- ~50% coverage (just essential interactions)

---

### 8.3: E2E Critical Path Tests
**Purpose**: Test complete user flows with mocked backend

**Files to Create**:
```
tests/e2e/setup.ts                        (~100 lines)
tests/e2e/game-flow.test.ts               (~150 lines)
tests/e2e/character-selection.test.ts     (~80 lines)
tests/e2e/chronicle.test.ts               (~100 lines)
```

**Mock Backend Setup**:
- Use Mock Service Worker (MSW) or similar
- Define handlers for all API endpoints
- Return realistic mock data
- Simulate delays and errors

**Critical Paths to Test**:
1. **New Game Flow**:
   - Start at GameListScreen
   - Click "New Game"
   - Select character
   - Select scenario
   - Game created
   - Enters GameInterfaceScreen

2. **Load Existing Game**:
   - Start at GameListScreen
   - Click on saved game
   - Loads GameInterfaceScreen
   - Game state displays correctly

3. **Chronicle CRUD**:
   - Open chronicle panel
   - Create new entry
   - Entry appears in list
   - Edit entry
   - Delete entry

4. **Send Message**:
   - Type message in chat
   - Submit
   - Message appears in history
   - Loading indicator shows
   - SSE response received (mocked)
   - Response appears in chat

**Testing Tools**:
- Vitest for test runner
- Testing Library for DOM queries
- MSW for API mocking
- JSDOM for browser environment

**Example**:
```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { screen, waitFor } from '@testing-library/dom';

const server = setupServer(
  http.get('/api/game/list', () => {
    return HttpResponse.json({
      saves: [
        { game_id: '1', scenario_name: 'Test', character_name: 'Hero', ... }
      ]
    });
  }),
  // More handlers...
);

beforeAll(() => server.listen());
afterAll(() => server.close());

describe('New Game Flow', () => {
  it('should create new game and enter game interface', async () => {
    // Initialize app
    await initializeApp();

    // Should be on game list screen
    expect(screen.getByText('Saved Games')).toBeInTheDocument();

    // Click "New Game"
    screen.getByText('New Game').click();

    // Should navigate to character selection
    await waitFor(() => {
      expect(screen.getByText('Select Your Character')).toBeInTheDocument();
    });

    // Select character
    screen.getByText('Aldric Swiftarrow').click();
    screen.getByText('Next').click();

    // Should navigate to scenario selection
    await waitFor(() => {
      expect(screen.getByText('Select Your Scenario')).toBeInTheDocument();
    });

    // Select scenario and start
    screen.getByText('The Lost Mine').click();
    screen.getByText('Start Game').click();

    // Should create game and navigate to game interface
    await waitFor(() => {
      expect(screen.getByText('Chat')).toBeInTheDocument();
      expect(screen.getByText('Party')).toBeInTheDocument();
      expect(screen.getByText('Location')).toBeInTheDocument();
    });
  });
});
```

**Coverage Target**:
- 4 critical paths tested
- Mock all backend responses
- ~70% confidence in core flows

---

### Phase 8 Summary
**Files Created**: 13 test files
**Lines of Code**: ~1,550 lines of tests
**Dependencies**: Vitest, Testing Library, MSW
**Definition of Done**:
- ✅ All service methods tested
- ✅ Critical components tested
- ✅ E2E critical paths tested
- ✅ All tests passing
- ✅ Coverage reports generated

---

## Implementation Order

**Recommended order to maximize deliverability**:

1. **Phase 5** (Screens & Navigation) - Foundation for everything else
2. **Phase 6.1** (Chronicle Panel) - High value feature
3. **Phase 6.2** (Tool Call Display) - Quick win
4. **Phase 6.3-6.5** (Character Sheet + Inventory + Toggle) - Related features
5. **Phase 7** (Catalog Browser) - Standalone feature
6. **Phase 8** (Testing) - Final polish

---

## Definitions of Done

### MVP Complete (Feature Parity)
- ✅ All Phase 5 screens working
- ✅ All Phase 6 components working
- ✅ All Phase 7 catalog features working
- ✅ Basic testing coverage (Phase 8)
- ✅ Zero TypeScript errors
- ✅ Zero `any` types
- ✅ All features from old frontend replicated
- ✅ SOLID principles followed
- ✅ Clean architecture maintained
- ✅ Fail-fast validation everywhere

### Ready for Production
- ✅ MVP Complete
- ✅ All tests passing
- ✅ No console errors in normal usage
- ✅ Responsive layout works
- ✅ Browser back button works
- ✅ Error states handled gracefully
- ✅ Loading states for all async operations

---

## Estimates

### Lines of Code (approximate)
- **Phase 5**: ~1,100 lines (TS + CSS)
- **Phase 6**: ~1,900 lines (TS + CSS)
- **Phase 7**: ~880 lines (TS + CSS)
- **Phase 8**: ~1,550 lines (tests)
- **Total New Code**: ~5,430 lines

### Time Estimates (rough)
- **Phase 5**: 1-2 days (screens + navigation)
- **Phase 6**: 2-3 days (components + CRUD)
- **Phase 7**: 1 day (catalog browser)
- **Phase 8**: 1-2 days (testing)
- **Total**: 5-8 days

---

## What to AVOID (Anti-Patterns)

To prevent over-engineering:

### ❌ DO NOT:
- Add state management libraries (Redux, MobX, etc.) - Observable is sufficient
- Add routing libraries (React Router, etc.) - Hash routing is sufficient
- Add UI frameworks (React, Vue, etc.) - Vanilla TS is working great
- Add form validation libraries - Custom validation is simple
- Add animation libraries - CSS transitions are enough
- Add date libraries - Native Date is fine for our use case
- Add markdown rendering libraries - HTML is sufficient for chronicle
- Build a complex component library - Keep it simple
- Over-abstract - Only abstract when you have 3+ identical patterns
- Add complex build optimizations - Vite handles it
- Add service workers - Not needed for MVP
- Add complex caching strategies - Keep it simple
- Build a design system - Just use consistent CSS
- Add i18n/l10n - English only for MVP
- Add analytics - Not needed yet
- Add feature flags - YAGNI

### ✅ DO:
- Keep files under 200 lines
- Follow existing patterns (Component, Screen, Service)
- Use existing utilities (dom.ts, Observable, StateStore)
- Fail fast with validation
- Write tests for services (high ROI)
- Keep CSS modular but in one file (main.css)
- Use TypeScript strict mode
- Handle errors explicitly
- Clean up subscriptions
- Document complex logic with comments

---

## Architecture Principles (Reminder)

### SOLID
- **S**ingle Responsibility: One class/function = one job
- **O**pen/Closed: Extend via composition, not modification
- **L**iskov Substitution: Components are polymorphic via base class
- **I**nterface Segregation: Focused service interfaces
- **D**ependency Inversion: Inject dependencies, depend on abstractions

### KISS (Keep It Simple, Stupid)
- Simplest solution that works
- No premature optimization
- No speculative features
- Clear, readable code over clever code

### DRY (Don't Repeat Yourself)
- Extract common logic to services/utils
- But don't over-abstract
- Three strikes rule: Duplicate twice, abstract on third

### Clean Architecture
- **Layers**: UI → Controllers → Services → Domain
- **Dependencies**: Flow inward (UI depends on services, not vice versa)
- **Boundaries**: Clear interfaces between layers

### Fail Fast
- Validate at boundaries
- Throw explicit errors
- No silent failures
- Type safety catches errors at compile time

---

## Success Criteria

### Technical
- [ ] TypeScript strict mode: zero errors
- [ ] Zero `any` types used
- [ ] Test coverage: >60% for services
- [ ] No memory leaks (verified with Chrome DevTools)
- [ ] No console errors in normal operation
- [ ] All SOLID principles followed
- [ ] All files under 200 lines (rare exceptions OK)

### Functional
- [ ] 100% feature parity with old frontend
- [ ] All user flows work end-to-end
- [ ] Loading states everywhere async
- [ ] Error states everywhere failures possible
- [ ] Navigation works (forward, back, URL)
- [ ] Chronicle CRUD works completely
- [ ] Catalog filtering matches old frontend exactly
- [ ] Character sheet shows all data
- [ ] Inventory shows all data
- [ ] Tool calls display correctly

### User Experience
- [ ] Responsive (works on 1920x1080 down to 1280x720)
- [ ] Fast (<100ms for UI interactions)
- [ ] Clear error messages
- [ ] Consistent styling (dark theme)
- [ ] Intuitive navigation
- [ ] No broken states (always can return to valid state)

---

## Next Steps

1. Review this plan with stakeholders
2. Confirm priorities and scope
3. Begin Phase 5 implementation
4. Iterate on each phase
5. Test thoroughly
6. Ship MVP!

---

Last Updated: 2025-11-05
