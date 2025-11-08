# Frontend-v2 Refactoring Plan

**Goal**: Transform frontend-v2 into a long-term stable, production-ready codebase that is fully SOLID, DRY, KISS, clean architecture, modular, with all files < 500 lines, all methods < 100 lines, comprehensive unit tests, and unified macOS-like + D&D fantasy styling.

**Approach**: Comprehensive refactoring with breaking changes allowed. No backward compatibility required.

---

## Phase 1: CSS Architecture & Design System

**Goal**: Break down 3,491-line main.css into modular files with a comprehensive design token system. Establish unified macOS + D&D visual language.

### 1.1 Design Token System
- [ ] Create `styles/core/variables.css` with comprehensive design tokens
  - [ ] Define D&D-themed color palette (parchment, stone, ember, arcane, nature, gold)
  - [ ] Define macOS-inspired semantic colors (bg, text, border, surface)
  - [ ] Define spacing scale (0.25rem to 4rem, following 4px base grid)
  - [ ] Define typography scale (font sizes, weights, line heights)
  - [ ] Define border radius tokens (subtle rounded corners)
  - [ ] Define shadow tokens (macOS-style depth)
  - [ ] Define z-index scale (modal, dropdown, toast)
  - [ ] Define transition/animation tokens (ease curves, durations)
- [ ] Create `styles/core/reset.css` (CSS reset/normalize)
- [ ] Create `styles/core/utilities.css` (common utility classes)
- [ ] Create `styles/core/typography.css` (base font styles, headings)

### 1.2 Component CSS Splitting
- [ ] Create `styles/components/` directory
- [ ] Split main.css into component-scoped files (each < 200 lines):
  - [ ] `button.css` - All button variants and states
  - [ ] `input.css` - Input fields, textareas, selects
  - [ ] `modal.css` - Modal overlay and dialog
  - [ ] `toast.css` - Toast notification styles
  - [ ] `chat-panel.css` - Chat interface styles
  - [ ] `chat-message.css` - Message bubbles and types
  - [ ] `chat-input.css` - Chat input area
  - [ ] `loading-indicator.css` - Loading/thinking animations
  - [ ] `party-panel.css` - Party sidebar styles
  - [ ] `party-member-card.css` - Member cards and stats
  - [ ] `location-panel.css` - Location display
  - [ ] `combat-panel.css` - Combat tracker
  - [ ] `combat-suggestion-card.css` - Suggestion UI
  - [ ] `chronicle-panel.css` - Chronicle/journal panel
  - [ ] `chronicle-entry.css` - Individual entries
  - [ ] `chronicle-filters.css` - Tab and filter UI
  - [ ] `journal-modal.css` - Journal entry editor
  - [ ] `character-sheet.css` - Character sheet container
  - [ ] `abilities-section.css` - Ability scores grid
  - [ ] `skills-section.css` - Skills list
  - [ ] `spells-section.css` - Spell list and slots
  - [ ] `attacks-section.css` - Attack/weapon list
  - [ ] `features-section.css` - Features and traits
  - [ ] `inventory-panel.css` - Inventory container
  - [ ] `equipment-slots.css` - Equipment slot grid
  - [ ] `item-list.css` - Item list and cards
  - [ ] `currency-display.css` - Currency UI
  - [ ] `header-bar.css` - Top header with game info
  - [ ] `game-list.css` - Game list screen
  - [ ] `game-list-item.css` - Individual game cards
  - [ ] `character-selection.css` - Character selection screen
  - [ ] `character-card.css` - Character option cards
  - [ ] `scenario-selection.css` - Scenario selection screen
  - [ ] `scenario-card.css` - Scenario option cards
  - [ ] `catalog-browser.css` - Catalog screen
  - [ ] `catalog-sidebar.css` - Catalog navigation
  - [ ] `catalog-item-list.css` - Item list view
  - [ ] `catalog-item-detail.css` - Item detail view
  - [ ] `content-pack-filter.css` - Content pack selector
  - [ ] `tool-call-message.css` - Tool execution messages

### 1.3 Layout CSS
- [ ] Create `styles/layout/` directory
- [ ] Extract layout-specific styles:
  - [ ] `game-interface.css` - Main 3-panel game layout
  - [ ] `panels.css` - Panel sizing, borders, scrolling
  - [ ] `screens.css` - Screen-level containers
  - [ ] `scrollbar.css` - Custom scrollbar theming

### 1.4 Main CSS Assembly
- [ ] Rewrite `styles/main.css` to import only (target: < 100 lines)
  - [ ] Import core styles
  - [ ] Import layout styles
  - [ ] Import component styles
- [ ] Verify total CSS is functionally identical to original
- [ ] Update Vite config if needed for CSS imports

### 1.5 macOS + D&D Visual Refinement
- [ ] Apply macOS-inspired effects to panels:
  - [ ] Translucent backgrounds with backdrop blur
  - [ ] Subtle border highlights (1px rgba white/black)
  - [ ] Layered shadows for depth
  - [ ] Consistent border radius (6-8px)
- [ ] Apply D&D fantasy theming:
  - [ ] Parchment/stone color tones
  - [ ] Gold/ember accent colors for important actions
  - [ ] Arcane blue for magical elements
  - [ ] Nature green for healing/success
- [ ] Refine button styles:
  - [ ] Primary buttons: arcane gradient with glow
  - [ ] Secondary buttons: subtle stone background
  - [ ] Danger buttons: ember gradient
  - [ ] Hover states: subtle lift + shadow
  - [ ] Active states: inset shadow
- [ ] Refine input styles:
  - [ ] Dark stone background with inner shadow
  - [ ] Subtle border with focus glow
  - [ ] Placeholder text with reduced opacity
- [ ] Ensure all animations use consistent easing (ease-out for entrances, ease-in-out for interactions)

---

## Phase 2: Service Layer Extraction

**Goal**: Extract business logic from screens and components into focused service classes following clean architecture.

### 2.1 Domain Services
- [ ] Create `src/services/domain/` directory
- [ ] Create `ToolResultFormatterService.ts`
  - [ ] Extract tool result formatting logic from GameInterfaceScreen (lines 294-340)
  - [ ] Methods: `formatLevelUp()`, `formatDiceRoll()`, `formatGeneric()`
  - [ ] Add unit tests for all formatting methods
- [ ] Create `ChronicleAggregatorService.ts`
  - [ ] Extract chronicle entry aggregation from ChroniclePanel (lines 252-346)
  - [ ] Methods: `aggregateWorldMemories()`, `aggregateLocationMemories()`, `aggregateNpcMemories()`, `aggregatePlayerJournal()`
  - [ ] Add unit tests for aggregation logic
- [ ] Create `ChronicleFilterService.ts`
  - [ ] Extract filtering logic from ChroniclePanel (lines 416-449)
  - [ ] Methods: `filterByTab()`, `filterBySearch()`, `sortEntries()`
  - [ ] Add unit tests for filter combinations
- [ ] Create `StreamingMessageService.ts`
  - [ ] Encapsulate streaming message state management
  - [ ] Methods: `startStream()`, `appendDelta()`, `endStream()`
  - [ ] Add unit tests for stream lifecycle

### 2.2 UI Builder Utilities
- [ ] Create `src/utils/ui-builders.ts`
  - [ ] `createHeader(title, className?)` - Standard header with title
  - [ ] `createSection(title, content, options?)` - Section with optional collapse
  - [ ] `createCard(content, options?)` - Card container with consistent styling
  - [ ] `createStatBar(label, current, max)` - HP/resource bar
  - [ ] `createBadge(text, variant)` - Colored badge (world/location/npc/player)
  - [ ] `createIconButton(icon, onClick)` - Icon-only button
  - [ ] `createEmptyState(message)` - Empty state placeholder
- [ ] Add unit tests for all UI builders

### 2.3 Formatting Utilities
- [ ] Create `src/utils/formatters.ts`
  - [ ] `formatTimestamp(isoString)` - Relative time (e.g., "2 hours ago")
  - [ ] `formatCurrency(copper, silver, gold, platinum)` - "10 gp, 5 sp"
  - [ ] `formatModifier(value)` - "+3" or "-1"
  - [ ] `formatDiceNotation(count, sides, modifier)` - "2d6+3"
  - [ ] `formatHitPoints(current, max, temp)` - "45/50 (+5)"
- [ ] Add unit tests for all formatters

---

## Phase 3: Screen Refactoring

**Goal**: Break down GameInterfaceScreen (684 lines) and other large screens into modular coordinators. All screens < 400 lines, all methods < 100 lines.

### 3.1 GameInterfaceScreen Decomposition
- [ ] Create `src/screens/game/` directory
- [ ] Create `SseEventHandlers.ts` (target: < 200 lines)
  - [ ] Extract all SSE event registration and handling (lines 179-477)
  - [ ] Use declarative handler map pattern
  - [ ] Inject dependencies: chatPanel, stateStore, gameId, toolFormatter
  - [ ] Methods: `registerAll()`, individual handler methods (< 30 lines each)
- [ ] Create `LeftPanelCoordinator.ts` (target: < 150 lines)
  - [ ] Manage LocationPanel, CombatPanel, ChroniclePanel
  - [ ] Handle panel lifecycle (mount/unmount)
  - [ ] Coordinate panel visibility based on game state
- [ ] Create `RightPanelCoordinator.ts` (target: < 150 lines)
  - [ ] Manage PartyPanel, CharacterSheetPanel, InventoryPanel
  - [ ] Handle panel switching logic (extract from GameInterfaceScreen lines 550-592)
  - [ ] Subscribe to rightPanelView changes
- [ ] Create `CenterPanelCoordinator.ts` (target: < 100 lines)
  - [ ] Manage ChatPanel and CombatSuggestionCard
  - [ ] Handle message sending and suggestion actions
- [ ] Refactor `GameInterfaceScreen.ts` (target: < 300 lines)
  - [ ] Use coordinators instead of managing components directly
  - [ ] Delegate SSE setup to SseEventHandlers
  - [ ] Delegate panel management to coordinators
  - [ ] Keep only: screen lifecycle, coordinator initialization, high-level coordination

### 3.2 ChroniclePanel Refactoring
- [ ] Refactor `ChroniclePanel.ts` (target: < 300 lines)
  - [ ] Use ChronicleAggregatorService for entry aggregation
  - [ ] Use ChronicleFilterService for filtering/sorting
  - [ ] Extract modal management to separate method (< 50 lines)
  - [ ] Simplify render logic using UI builders

### 3.3 Other Screen Improvements
- [ ] Review `ScenarioSelectionScreen.ts` (351 lines)
  - [ ] Extract content pack selection logic to separate method
  - [ ] Extract scenario rendering to separate method
  - [ ] Ensure all methods < 100 lines
- [ ] Review `CatalogBrowserScreen.ts` (263 lines)
  - [ ] Extract sidebar/detail coordination to separate methods
  - [ ] Ensure all methods < 100 lines

---

## Phase 4: Component Refactoring

**Goal**: Refactor large components to use extracted services and UI builders. All components < 300 lines, all methods < 100 lines.

### 4.1 Chat Components
- [ ] Refactor `ChatPanel.ts` (376 lines → target: < 250 lines)
  - [ ] Use StreamingMessageService for streaming messages
  - [ ] Extract ally suggestion button logic to separate method
  - [ ] Use UI builders for header/container creation
- [ ] Refactor `ChatMessage.ts` (334 lines → target: < 250 lines)
  - [ ] Extract message type rendering to separate methods (< 50 lines each)
  - [ ] Use formatters for timestamps
  - [ ] Use UI builders for message containers

### 4.2 Combat Components
- [ ] Refactor `CombatPanel.ts` (319 lines → target: < 250 lines)
  - [ ] Extract participant rendering to separate method
  - [ ] Extract turn indicator logic to separate method
  - [ ] Use UI builders for combat tracker UI

### 4.3 Header Component
- [ ] Refactor `HeaderBar.ts` (280 lines → target: < 200 lines)
  - [ ] Extract location rendering to separate method
  - [ ] Extract combat indicator logic to separate method
  - [ ] Extract action buttons to separate method

### 4.4 Inventory Components
- [ ] Refactor `InventoryPanel.ts` (276 lines → target: < 200 lines)
  - [ ] Extract tab switching logic to separate method
  - [ ] Use UI builders for panel structure
  - [ ] Use formatters for currency display

### 4.5 Character Sheet Components
- [ ] Refactor `CharacterSheetPanel.ts` (239 lines → target: < 200 lines)
  - [ ] Use UI builders for tab navigation
  - [ ] Extract tab rendering to separate methods

### 4.6 Party Components
- [ ] Refactor `PartyPanel.ts` (205 lines → target: < 150 lines)
  - [ ] Use UI builders for member card containers
  - [ ] Extract stat bar rendering to separate method

---

## Phase 5: Component Testing

**Goal**: Achieve comprehensive unit test coverage for all components. Focus on core behavior, lifecycle, and state management.

### 5.1 Base Component Tests
- [ ] Create `src/components/base/__tests__/Component.test.ts`
  - [ ] Test lifecycle: mount, update, unmount
  - [ ] Test subscription cleanup on unmount
  - [ ] Test re-rendering on update
  - [ ] Test isMountedToDOM state tracking

### 5.2 Chat Component Tests
- [ ] Create `src/components/chat/__tests__/ChatPanel.test.ts`
  - [ ] Test message rendering from game state
  - [ ] Test real-time message addition
  - [ ] Test message updates (streaming)
  - [ ] Test processing state (loading indicator)
  - [ ] Test input enable/disable
- [ ] Create `src/components/chat/__tests__/ChatMessage.test.ts`
  - [ ] Test different message types (user, assistant, system, tool, npc)
  - [ ] Test timestamp formatting
  - [ ] Test metadata display
- [ ] Create `src/components/chat/__tests__/ChatInput.test.ts`
  - [ ] Test submit on Enter
  - [ ] Test new line on Shift+Enter
  - [ ] Test disabled state
  - [ ] Test placeholder changes
- [ ] Create `src/components/chat/__tests__/LoadingIndicator.test.ts`
  - [ ] Test agent type display
  - [ ] Test animation presence

### 5.3 Party Component Tests
- [ ] Create `src/components/party/__tests__/PartyPanel.test.ts`
  - [ ] Test member rendering from game state
  - [ ] Test selection handling
  - [ ] Test empty state
- [ ] Create `src/components/party/__tests__/PartyMemberCard.test.ts`
  - [ ] Test stat bar calculations
  - [ ] Test condition badges
  - [ ] Test HP display formatting

### 5.4 Character Sheet Tests
- [ ] Create `src/components/character-sheet/__tests__/CharacterSheetPanel.test.ts`
  - [ ] Test tab switching
  - [ ] Test section rendering based on selected tab
- [ ] Create `src/components/character-sheet/__tests__/AbilitiesSection.test.ts`
  - [ ] Test ability score display
  - [ ] Test modifier calculations
  - [ ] Test saving throw display
- [ ] Create `src/components/character-sheet/__tests__/SkillsSection.test.ts`
  - [ ] Test skill list rendering
  - [ ] Test proficiency bonus display
- [ ] Create `src/components/character-sheet/__tests__/SpellsSection.test.ts`
  - [ ] Test spell slot display
  - [ ] Test spell list by level
  - [ ] Test empty state for non-casters
- [ ] Create `src/components/character-sheet/__tests__/AttacksSection.test.ts`
  - [ ] Test attack list rendering
  - [ ] Test damage formatting
- [ ] Create `src/components/character-sheet/__tests__/FeaturesSection.test.ts`
  - [ ] Test feature list rendering
  - [ ] Test collapsible feature descriptions

### 5.5 Inventory Component Tests
- [ ] Create `src/components/inventory/__tests__/InventoryPanel.test.ts`
  - [ ] Test tab switching (inventory vs equipment)
  - [ ] Test panel rendering
- [ ] Create `src/components/inventory/__tests__/EquipmentSlots.test.ts`
  - [ ] Test slot rendering
  - [ ] Test equipped item display
  - [ ] Test empty slot placeholders
- [ ] Create `src/components/inventory/__tests__/ItemList.test.ts`
  - [ ] Test item rendering
  - [ ] Test quantity display
- [ ] Create `src/components/inventory/__tests__/CurrencyDisplay.test.ts`
  - [ ] Test currency formatting
  - [ ] Test currency conversions

### 5.6 Chronicle Component Tests
- [ ] Create `src/components/chronicle/__tests__/ChroniclePanel.test.ts`
  - [ ] Test tab filtering (all, world, locations, npcs, notes)
  - [ ] Test search functionality
  - [ ] Test location filter toggle
  - [ ] Test entry rendering
  - [ ] Test add/edit/delete flows
- [ ] Create `src/components/chronicle/__tests__/ChronicleEntry.test.ts`
  - [ ] Test entry display
  - [ ] Test badge rendering
  - [ ] Test timestamp display
  - [ ] Test tag rendering
- [ ] Create `src/components/chronicle/__tests__/ChronicleFilters.test.ts`
  - [ ] Test active tab state
  - [ ] Test search input
  - [ ] Test filter checkbox

### 5.7 Combat Component Tests
- [ ] Create `src/components/combat/__tests__/CombatPanel.test.ts`
  - [ ] Test participant rendering
  - [ ] Test initiative order
  - [ ] Test current turn indicator
  - [ ] Test faction display
- [ ] Create `src/components/combat/__tests__/CombatSuggestionCard.test.ts`
  - [ ] Test suggestion display
  - [ ] Test accept action
  - [ ] Test override action
  - [ ] Test hide/show logic

### 5.8 Location Component Tests
- [ ] Create `src/components/location/__tests__/LocationPanel.test.ts`
  - [ ] Test location name display
  - [ ] Test danger level indicator
  - [ ] Test NPC list rendering

### 5.9 Header Component Tests
- [ ] Create `src/components/header/__tests__/HeaderBar.test.ts`
  - [ ] Test location display
  - [ ] Test time display
  - [ ] Test combat indicator
  - [ ] Test agent indicator
  - [ ] Test action buttons (save, exit, catalogs)

### 5.10 Common Component Tests
- [ ] Create `src/components/common/__tests__/Modal.test.ts`
  - [ ] Test modal rendering
  - [ ] Test button actions
  - [ ] Test ESC key dismiss
  - [ ] Test overlay click dismiss
  - [ ] Test confirm() helper
  - [ ] Test alert() helper
- [ ] Create `src/components/common/__tests__/Toast.test.ts`
  - [ ] Test toast display
  - [ ] Test auto-dismiss
  - [ ] Test multiple toasts
  - [ ] Test different types (success, error, info)

### 5.11 Base Component Tests
- [ ] Create `src/components/base/__tests__/CollapsibleSection.test.ts`
  - [ ] Test expand/collapse toggle
  - [ ] Test content visibility
  - [ ] Test icon rotation

### 5.12 Screen Component Tests
- [ ] Create `src/components/scenario/__tests__/ScenarioCard.test.ts`
  - [ ] Test scenario rendering
  - [ ] Test selection handling
- [ ] Create `src/components/character/__tests__/CharacterCard.test.ts`
  - [ ] Test character rendering
  - [ ] Test selection handling
- [ ] Create `src/components/game/__tests__/GameListItem.test.ts`
  - [ ] Test game info display
  - [ ] Test action buttons (load, delete)

### 5.13 Catalog Component Tests
- [ ] Create `src/components/catalog/__tests__/CatalogSidebar.test.ts`
  - [ ] Test category selection
  - [ ] Test active state
- [ ] Create `src/components/catalog/__tests__/CatalogItemList.test.ts`
  - [ ] Test item list rendering
  - [ ] Test selection handling
- [ ] Create `src/components/catalog/__tests__/CatalogItemDetail.test.ts`
  - [ ] Test item detail display
  - [ ] Test close action
- [ ] Create `src/components/catalog/__tests__/ContentPackFilter.test.ts`
  - [ ] Test pack selection
  - [ ] Test checkbox state

---

## Phase 6: Utility Testing

**Goal**: Test all utility functions to ensure robust helper layer.

### 6.1 DOM Utility Tests
- [ ] Create `src/utils/__tests__/dom.test.ts`
  - [ ] Test createElement with attributes
  - [ ] Test createElement with children
  - [ ] Test event listener registration
  - [ ] Test convenience functions (div, span, button)
  - [ ] Test escapeHtml (XSS prevention)
  - [ ] Test clearElement
  - [ ] Test class manipulation (addClass, removeClass, toggleClass)
  - [ ] Test query helpers

### 6.2 UI Builder Tests
- [ ] Create `src/utils/__tests__/ui-builders.test.ts`
  - [ ] Test createHeader
  - [ ] Test createSection
  - [ ] Test createCard
  - [ ] Test createStatBar with various values
  - [ ] Test createBadge variants
  - [ ] Test createIconButton
  - [ ] Test createEmptyState

### 6.3 Formatter Tests
- [ ] Create `src/utils/__tests__/formatters.test.ts`
  - [ ] Test formatTimestamp (now, minutes ago, hours ago, days ago)
  - [ ] Test formatCurrency (various combinations)
  - [ ] Test formatModifier (positive, negative, zero)
  - [ ] Test formatDiceNotation
  - [ ] Test formatHitPoints (normal, temp HP, max HP)

### 6.4 Markdown Utility Tests
- [ ] Create `src/utils/__tests__/markdown.test.ts`
  - [ ] Test markdown parsing
  - [ ] Test XSS prevention
  - [ ] Test link rendering

### 6.5 Catalog Filter Tests
- [ ] Create `src/utils/__tests__/catalogFilters.test.ts`
  - [ ] Test filtering by content pack
  - [ ] Test filtering by category
  - [ ] Test search filtering

### 6.6 Item Slot Validation Tests
- [ ] Create `src/utils/__tests__/itemSlotValidation.test.ts`
  - [ ] Test valid slot assignments
  - [ ] Test invalid slot assignments
  - [ ] Test two-handed weapon conflicts

---

## Phase 7: Service Testing

**Goal**: Test all domain services extracted in Phase 2.

### 7.1 Domain Service Tests
- [ ] Create `src/services/domain/__tests__/ToolResultFormatterService.test.ts`
  - [ ] Test formatLevelUp
  - [ ] Test formatDiceRoll (normal, critical, critical fail)
  - [ ] Test formatGeneric for unknown result types
- [ ] Create `src/services/domain/__tests__/ChronicleAggregatorService.test.ts`
  - [ ] Test aggregateWorldMemories
  - [ ] Test aggregateLocationMemories (current location only)
  - [ ] Test aggregateLocationMemories (all locations)
  - [ ] Test aggregateNpcMemories (current location only)
  - [ ] Test aggregateNpcMemories (all locations)
  - [ ] Test aggregatePlayerJournal
  - [ ] Test combined aggregation
- [ ] Create `src/services/domain/__tests__/ChronicleFilterService.test.ts`
  - [ ] Test filterByTab (all, world, locations, npcs, notes)
  - [ ] Test filterBySearch (content, tags, NPC names)
  - [ ] Test sortEntries (pinned first, then by date)
  - [ ] Test combined filtering + sorting
- [ ] Create `src/services/domain/__tests__/StreamingMessageService.test.ts`
  - [ ] Test stream lifecycle (start, append, end)
  - [ ] Test buffer accumulation
  - [ ] Test message key tracking
  - [ ] Test multiple concurrent streams

---

## Phase 8: Coordinator Testing

**Goal**: Test screen coordinators extracted in Phase 3.

### 8.1 GameInterfaceScreen Coordinator Tests
- [ ] Create `src/screens/game/__tests__/SseEventHandlers.test.ts`
  - [ ] Test handler registration
  - [ ] Test each event handler with mock events
  - [ ] Test error handling in handlers
- [ ] Create `src/screens/game/__tests__/LeftPanelCoordinator.test.ts`
  - [ ] Test panel mounting
  - [ ] Test panel unmounting
  - [ ] Test panel lifecycle coordination
- [ ] Create `src/screens/game/__tests__/RightPanelCoordinator.test.ts`
  - [ ] Test panel switching (party, character-sheet, inventory)
  - [ ] Test panel unmounting before switch
  - [ ] Test panel remounting
- [ ] Create `src/screens/game/__tests__/CenterPanelCoordinator.test.ts`
  - [ ] Test message sending
  - [ ] Test suggestion handling

---

## Phase 9: Code Quality & Linting

**Goal**: Enforce code quality standards via tooling to prevent regressions.

### 9.1 ESLint Configuration
- [ ] Update `.eslintrc.json` with strict rules:
  - [ ] `max-lines: ["error", 500]` - Enforce file line limit
  - [ ] `max-lines-per-function: ["error", 100]` - Enforce method line limit
  - [ ] `complexity: ["error", 10]` - Limit cyclomatic complexity
  - [ ] `max-depth: ["error", 4]` - Limit nesting depth
  - [ ] `max-params: ["error", 4]` - Limit function parameters
  - [ ] `no-duplicate-imports: "error"` - Prevent duplicate imports
  - [ ] `@typescript-eslint/explicit-function-return-type: "warn"` - Encourage return types
  - [ ] `@typescript-eslint/no-explicit-any: "error"` - Ban `any`

### 9.2 Prettier Configuration
- [ ] Update `.prettierrc` for consistent formatting:
  - [ ] `printWidth: 100` - Match line length preference
  - [ ] `singleQuote: true` - Use single quotes
  - [ ] `trailingComma: "es5"` - Trailing commas where valid

### 9.3 Git Hooks
- [ ] Set up husky + lint-staged
  - [ ] Pre-commit: Run ESLint on staged files
  - [ ] Pre-commit: Run Prettier on staged files
  - [ ] Pre-commit: Run unit tests on changed files

### 9.4 CI/CD Integration
- [ ] Add GitHub Actions workflow (or equivalent):
  - [ ] Lint check (ESLint)
  - [ ] Format check (Prettier)
  - [ ] Type check (TypeScript)
  - [ ] Unit tests (Vitest)
  - [ ] Build check (Vite)

---

## Phase 10: Documentation & Polish

**Goal**: Ensure codebase is well-documented and ready for long-term maintenance.

### 10.1 README Updates
- [ ] Update `frontend-v2/README.md`:
  - [ ] Document new folder structure
  - [ ] Document component architecture (Component base class, coordinators pattern)
  - [ ] Document state management (Observable pattern, StateStore)
  - [ ] Document styling approach (BEM + design tokens)
  - [ ] Document testing strategy (Vitest, what's tested)
  - [ ] Update development commands (dev, build, test, lint)
  - [ ] Add troubleshooting section

### 10.2 Code Documentation
- [ ] Add JSDoc comments to all public APIs:
  - [ ] Component classes (constructor, public methods)
  - [ ] Service classes (all methods)
  - [ ] Utility functions (all exported functions)
  - [ ] Coordinator classes (all methods)
- [ ] Add inline comments for complex logic (> 10 lines)

### 10.3 Type Safety Review
- [ ] Review all files for proper TypeScript usage:
  - [ ] No `any` types (use `unknown` with type guards)
  - [ ] Explicit return types on all functions
  - [ ] Proper null handling (`?? null`, optional chaining)
  - [ ] Discriminated unions where applicable

### 10.4 Final Verification
- [ ] Run full linting pass - fix all errors/warnings
- [ ] Run full test suite - achieve > 80% coverage
- [ ] Run build - ensure no errors
- [ ] Manual testing of all screens:
  - [ ] Game list screen
  - [ ] Character selection screen
  - [ ] Scenario selection screen
  - [ ] Game interface screen (all panels)
  - [ ] Catalog browser screen
- [ ] Manual testing of all features:
  - [ ] Chat (send message, streaming narrative)
  - [ ] Combat (turn tracking, suggestions)
  - [ ] Chronicle (filtering, search, journal CRUD)
  - [ ] Character sheet (all tabs)
  - [ ] Inventory (equipment, items)
  - [ ] Party (member selection)
- [ ] Visual QA for design consistency:
  - [ ] Verify all buttons use design tokens
  - [ ] Verify all panels have consistent styling
  - [ ] Verify all spacing uses design tokens
  - [ ] Verify all colors use design tokens
  - [ ] Check hover states on all interactive elements
  - [ ] Check focus states for accessibility

---

## Phase 11: Final Cleanup

**Goal**: Remove dead code, consolidate patterns, ensure codebase is pristine.

### 11.1 Dead Code Removal
- [ ] Search for unused imports across all files
- [ ] Search for unused variables/functions
- [ ] Remove commented-out code
- [ ] Remove debug console.logs (keep only essential logging)

### 11.2 Import Organization
- [ ] Organize imports consistently:
  - [ ] External packages (react, etc.)
  - [ ] Internal aliases (@/)
  - [ ] Relative imports (./...)
  - [ ] Types (type imports)
- [ ] Use barrel exports (index.ts) for common exports

### 11.3 Naming Consistency
- [ ] Review class names (PascalCase)
- [ ] Review method names (camelCase)
- [ ] Review file names (kebab-case for components, PascalCase for classes)
- [ ] Review CSS class names (BEM: block__element--modifier)

### 11.4 Pattern Consolidation
- [ ] Ensure all components use same lifecycle pattern
- [ ] Ensure all services use same injection pattern
- [ ] Ensure all coordinators use same initialization pattern
- [ ] Ensure all tests use same setup/teardown pattern

---

## Success Criteria

### File Size Compliance
- [ ] ✅ All TypeScript files < 500 lines
- [ ] ✅ All CSS files < 200 lines
- [ ] ✅ main.css < 100 lines (imports only)

### Method Size Compliance
- [ ] ✅ All methods < 100 lines
- [ ] ✅ No deeply nested logic (max depth: 4)

### Code Quality
- [ ] ✅ No ESLint errors
- [ ] ✅ No TypeScript errors
- [ ] ✅ No `any` types
- [ ] ✅ All public APIs have JSDoc comments

### Testing
- [ ] ✅ All services have unit tests
- [ ] ✅ All utilities have unit tests
- [ ] ✅ All components have unit tests
- [ ] ✅ Test coverage > 80%

### Architecture
- [ ] ✅ Full SOLID compliance (no god objects, clear SRP, DIP via container)
- [ ] ✅ DRY (no duplicate logic, shared utilities)
- [ ] ✅ KISS (no over-engineering, clear abstractions)
- [ ] ✅ Clean architecture (domain layer, service layer, presentation layer)

### Design System
- [ ] ✅ Comprehensive design tokens (colors, spacing, typography, shadows, radius)
- [ ] ✅ Consistent macOS-like styling (translucent panels, subtle depth, rounded corners)
- [ ] ✅ D&D fantasy theming (parchment/stone tones, gold/ember/arcane accents)
- [ ] ✅ All components use design tokens (no hardcoded values)

### Documentation
- [ ] ✅ README.md is up-to-date with architecture
- [ ] ✅ All complex logic has inline comments
- [ ] ✅ All public APIs have JSDoc

---

## Notes

- **Breaking Changes**: Allowed - refactor freely for best architecture
- **Folder Structure**: Can be reorganized for better modularity
- **CSS Framework**: Evaluate UnoCSS or Tailwind if it simplifies token management; otherwise pure CSS with variables
- **Focus**: SOLID, DRY, KISS, clean architecture above all else
- **Timeline**: No deadline - prioritize quality and completeness
- **Testing**: Unit tests for components/services/utils only (no E2E, no visual regression)

---

## Getting Started

**Recommended Execution Order**:
1. Start with Phase 1 (CSS) - lowest risk, highest visual impact
2. Continue with Phase 2 (Services) - prepares for screen refactoring
3. Proceed with Phase 3 (Screens) - most complex, depends on Phase 2
4. Follow with Phase 4 (Components) - uses services from Phase 2
5. Complete Phase 5-8 (Testing) - can be done incrementally alongside refactoring
6. Finish with Phase 9-11 (Quality, Docs, Cleanup) - final polish

**Progress Tracking**: Check off items as completed. Each phase can be committed independently.

