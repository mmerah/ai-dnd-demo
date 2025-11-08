# Frontend-v2 Code Review

**Review Date**: 2025-11-08
**Scope**: TypeScript/Vite rewrite of legacy frontend
**Focus**: SOLID, DRY, KISS, Workability, Style Consistency

---

## Executive Summary

The frontend-v2 represents a **significant improvement** over the legacy codebase. The team has implemented:
- ✅ Strong architectural patterns (Component/Screen abstraction, DI container, Observable pattern)
- ✅ Type safety via auto-generated backend types
- ✅ Service layer separation (API, SSE, State)
- ✅ Test coverage for core services (6 test files covering StateStore, Observable, and API services)

**However**, there are critical violations of the stated quality standards that must be addressed:

### Critical Issues (Priority 1)
1. **GameInterfaceScreen.ts (684 lines)** - Exceeds 500-line limit by 37%
2. **ChroniclePanel.ts (534 lines)** - Exceeds limit by 7%
3. **main.css (3,491 lines)** - Exceeds limit by **598%** - massive monolith
4. **Inconsistent styling** - No design system, 30+ ad-hoc color values, mixed spacing patterns
5. **Zero UI component tests** - Only service-layer tests exist

### Moderate Issues (Priority 2)
6. Missing method-level decomposition (100+ line methods in screens)
7. Duplicate DOM construction patterns across components
8. CSS BEM naming inconsistency
9. No visual regression testing
10. Hardcoded colors/spacing throughout CSS

---

## 1. SOLID Principles Analysis

### ✅ Strengths

#### Single Responsibility Principle (SRP)
- **StateStore** - Clean separation of concerns with individual observables per concern
- **Service layer** - Well-separated: `ApiService` (HTTP), `GameApiService` (game logic), `SseService` (real-time)
- **Component base class** - Focused on lifecycle management only

#### Dependency Inversion Principle (DIP)
```typescript
// Excellent: Components depend on abstractions (StateStore interface), not concretions
export interface ServiceContainer {
  apiService: ApiService;
  gameApiService: GameApiService;
  catalogApiService: CatalogApiService;
  journalApiService: JournalApiService;
  stateStore: StateStore;
  sseService: SseService;
}
```

#### Open/Closed Principle (OCP)
- Component base class allows extension via lifecycle hooks
- Observable pattern allows adding subscribers without modifying core

### ⚠️ Violations

#### Interface Segregation Principle (ISP)
**Problem**: `GameInterfaceScreen` is a **god object** managing 9+ components:
```typescript
// Lines 33-44 - Too many responsibilities
private headerBar: HeaderBar | null = null;
private chatPanel: ChatPanel | null = null;
private combatSuggestionCard: CombatSuggestionCard | null = null;
private partyPanel: PartyPanel | null = null;
private characterSheetPanel: CharacterSheetPanel | null = null;
private inventoryPanel: InventoryPanel | null = null;
private locationPanel: LocationPanel | null = null;
private combatPanel: CombatPanel | null = null;
private chroniclePanel: ChroniclePanel | null = null;
```

**Fix**: Extract to specialized coordinators:
```typescript
// Proposed refactor
class LeftPanelCoordinator {
  private locationPanel: LocationPanel;
  private combatPanel: CombatPanel;
  private chroniclePanel: ChroniclePanel;
  // Manages only left panel lifecycle
}

class RightPanelCoordinator {
  private partyPanel: PartyPanel;
  private characterSheetPanel: CharacterSheetPanel;
  private inventoryPanel: InventoryPanel;
  // Manages panel switching logic
}

class GameInterfaceScreen {
  private leftPanel: LeftPanelCoordinator;
  private rightPanel: RightPanelCoordinator;
  private centerPanel: CenterPanelCoordinator;
  // Coordinates high-level screen concerns only
}
```

---

## 2. DRY Violations

### Critical Duplication: SSE Event Handler Pattern

**Location**: `GameInterfaceScreen.ts:179-477` (298 lines of handler registration)

**Problem**: Repetitive event handler registration:
```typescript
// Lines 181-224 - Pattern repeated 15+ times
container.sseService.on('connected', (event) => {
  console.log('[SSE] Connection established:', event);
});

container.sseService.on('initial_narrative', (event) => {
  console.log('[SSE] Initial narrative received');
  if (event.type === 'initial_narrative') {
    // ... 40+ lines of logic
  }
});

container.sseService.on('narrative', (event) => {
  console.log('[SSE] Narrative received');
  if (event.type === 'narrative') {
    // ... defensive checks and logic
  }
});
```

**Fix**: Extract to declarative handler map:
```typescript
// src/screens/game/SseEventHandlers.ts
export class SseEventHandlers {
  private handlers: Map<SseEventType, SseEventHandler>;

  constructor(
    private chatPanel: ChatPanel,
    private stateStore: StateStore,
    private gameId: string
  ) {
    this.handlers = this.createHandlerMap();
  }

  registerAll(sseService: SseService): void {
    this.handlers.forEach((handler, eventType) => {
      sseService.on(eventType, handler);
    });
  }

  private createHandlerMap(): Map<SseEventType, SseEventHandler> {
    return new Map([
      ['connected', this.handleConnected],
      ['initial_narrative', this.handleInitialNarrative],
      ['narrative', this.handleNarrative],
      // ... rest of handlers
    ]);
  }

  private handleConnected = (event: TypedSseEvent<'connected'>): void => {
    console.log('[SSE] Connection established:', event);
  };

  private handleInitialNarrative = (event: TypedSseEvent<'initial_narrative'>): void => {
    // Extract 40+ lines of logic to dedicated method
    if (this.shouldSkipInitialNarrative()) return;
    this.addScenarioTitle(event.data.scenario_title);
    this.addNarrative(event.data.narrative, event.data.timestamp);
  };
}
```

### Duplicate DOM Construction

**Problem**: Every component manually constructs DOM elements:
```typescript
// Repeated in 30+ components
const header = createElement('div', { class: 'component__header' });
const title = createElement('h2', { class: 'component__title' });
title.textContent = 'Title';
header.appendChild(title);
```

**Fix**: Extract to reusable UI builder utilities:
```typescript
// src/utils/ui-builders.ts
export const createHeader = (title: string, className = 'component__header'): HTMLElement => {
  const header = div({ class: className });
  const titleEl = createElement('h2', { class: `${className}__title` });
  titleEl.textContent = title;
  header.appendChild(titleEl);
  return header;
};

export const createSectionWithHeader = (
  title: string,
  content: HTMLElement,
  options?: { collapsible?: boolean }
): HTMLElement => {
  const section = div({ class: 'section' });
  section.appendChild(createHeader(title));
  section.appendChild(content);
  if (options?.collapsible) {
    makeCollapsible(section);
  }
  return section;
};
```

---

## 3. KISS Violations

### Over-Engineered Streaming Logic

**Location**: `GameInterfaceScreen.ts:245-267`

**Problem**: Manages streaming state in the screen instead of the component:
```typescript
// Lines 46-48 - Leaky abstraction
private narrativeBuffer: string = '';
private narrativeMessageKey: string | null = null;

// Lines 245-267 - ChatPanel should own this
container.sseService.on('narrative_chunk', (event) => {
  if (event.type === 'narrative_chunk') {
    const delta = event.data.delta ?? '';

    if (!this.narrativeMessageKey) {
      this.narrativeBuffer = delta;
      this.narrativeMessageKey = this.chatPanel?.addRealtimeMessage({
        type: 'assistant',
        content: delta,
        timestamp: new Date().toISOString(),
      }) ?? null;
    } else {
      this.narrativeBuffer += delta;
      if (this.narrativeMessageKey) {
        this.chatPanel?.updateMessage(this.narrativeMessageKey, this.narrativeBuffer);
      }
    }
  }
});
```

**Fix**: Encapsulate in ChatPanel:
```typescript
// ChatPanel should expose:
public startStreamingMessage(): string {
  const key = `stream-${Date.now()}`;
  this.streamingMessages.set(key, { buffer: '', messageKey: null });
  return key;
}

public appendToStream(streamKey: string, delta: string): void {
  const stream = this.streamingMessages.get(streamKey);
  if (!stream) return;

  stream.buffer += delta;
  if (!stream.messageKey) {
    stream.messageKey = this.addRealtimeMessage({
      type: 'assistant',
      content: delta,
      timestamp: new Date().toISOString(),
    });
  } else {
    this.updateMessage(stream.messageKey, stream.buffer);
  }
}

public endStream(streamKey: string): void {
  this.streamingMessages.delete(streamKey);
}
```

---

## 4. Workability Issues

### 🔴 File Length Violations

| File | Lines | Limit | Violation |
|------|-------|-------|-----------|
| **main.css** | **3,491** | 500 | **+598%** 🚨 |
| GameInterfaceScreen.ts | 684 | 500 | +37% |
| ChroniclePanel.ts | 534 | 500 | +7% |

### 🔴 Method Length Violations

**GameInterfaceScreen.ts:179-477** - `setupSseEventHandlers()` is **298 lines** (limit: 100)

**ChroniclePanel.ts:252-346** - `aggregateEntries()` is **95 lines** (acceptable but near limit)

### 🟡 Missing Tests

**Coverage Analysis**:
- ✅ Service layer: 6 test files (StateStore, Observable, ApiService, GameApiService, CatalogApiService, JournalApiService)
- ❌ Components: **0 test files**
- ❌ Screens: **0 test files**
- ❌ Utils: **0 test files** (dom.ts, markdown.ts, etc.)

**Required**:
```typescript
// src/components/base/__tests__/Component.test.ts
describe('Component lifecycle', () => {
  it('should call onMount after mounting');
  it('should call onUnmount before unmounting');
  it('should clean up subscriptions on unmount');
});

// src/utils/__tests__/dom.test.ts
describe('createElement', () => {
  it('should create element with attributes');
  it('should handle event listeners');
  it('should prevent XSS via escapeHtml');
});
```

---

## 5. Style & Design System Issues

### 🔴 **CRITICAL: CSS Monolith (3,491 lines)**

**Problem**: Single massive stylesheet with:
- 30+ ad-hoc color values (no CSS variables for secondary colors)
- Inconsistent spacing (mix of px and CSS variables)
- No component-scoped styles
- No modern CSS architecture (no CSS modules, no scoped styles)

**Current Structure** (from grep analysis):
```css
/* 3,491 lines organized in 40+ sections */
/* ==================== Reset & Base ==================== */
/* ==================== Game Interface Screen ==================== */
/* ==================== Header Bar ==================== */
/* ==================== Button Utilities ==================== */
/* ==================== Chat Panel ==================== */
/* ... 35+ more sections ... */
```

**Fix Options**:

#### Option A: CSS Modules (Recommended)
```typescript
// Each component imports its own styles
import styles from './ChatPanel.module.css';

const panel = div({ class: styles.chatPanel });
const header = div({ class: styles.header });
```

**Structure**:
```
styles/
  ├── core/
  │   ├── reset.css
  │   ├── variables.css       # Design tokens
  │   └── typography.css
  ├── components/
  │   ├── ChatPanel.module.css
  │   ├── PartyPanel.module.css
  │   └── ...
  └── main.css                # < 100 lines - imports only
```

#### Option B: BEM + File Splitting
```
styles/
  ├── 00-core/
  │   ├── reset.css
  │   ├── variables.css
  │   └── utilities.css
  ├── 01-layout/
  │   ├── game-interface.css
  │   └── panels.css
  ├── 02-components/
  │   ├── chat-panel.css      # < 200 lines each
  │   ├── party-panel.css
  │   ├── chronicle-panel.css
  │   └── ...
  └── main.css                # Imports all
```

### 🟡 Inconsistent BEM Naming

**Found Patterns** (from component analysis):
```css
/* Good BEM */
.chat-panel__header
.chat-panel__messages
.chat-panel__input

/* Inconsistent */
.btn btn--small              /* Space-separated modifiers */
.modal__button--primary      /* Correct BEM modifier */
.chronicle-tab active        /* Missing BEM modifier syntax */
```

**Fix**: Enforce strict BEM:
```css
/* Always use -- for modifiers */
.btn--small
.btn--danger
.chronicle-tab--active

/* Always use __ for elements */
.modal__button
.modal__header
```

### 🟡 No Design Token System

**Problem**: Colors, spacing, and typography scattered throughout:
```css
/* Found in main.css */
color: #e0e0e0;              /* Line 14 */
color: #b0b0b0;              /* Line 15 */
color: #f87171;              /* Line 20 */
padding: 8px 16px;           /* Inline values */
font-size: 14px;             /* No scale */
```

**Fix**: Comprehensive design token system:
```css
/* styles/core/variables.css */
:root {
  /* Color Palette - D&D Fantasy Theme */
  --color-parchment-50: #fdfbf7;
  --color-parchment-100: #f5f0e8;
  --color-parchment-200: #ebe3d5;
  --color-parchment-900: #2a2520;

  --color-stone-50: #fafaf9;
  --color-stone-900: #1c1917;

  --color-ember-400: #fb923c;  /* Danger/Combat */
  --color-ember-600: #dc2626;

  --color-arcane-400: #818cf8;  /* Magic/Accent */
  --color-arcane-600: #4f46e5;

  --color-nature-400: #4ade80;  /* Success/Healing */
  --color-nature-600: #16a34a;

  /* Semantic Tokens */
  --color-bg-primary: var(--color-stone-900);
  --color-bg-secondary: #2a2a2a;
  --color-bg-tertiary: #3a3a3a;

  --color-text-primary: var(--color-parchment-100);
  --color-text-secondary: var(--color-parchment-200);
  --color-text-muted: #94a3b8;

  --color-accent: var(--color-arcane-400);
  --color-success: var(--color-nature-400);
  --color-warning: #fbbf24;
  --color-danger: var(--color-ember-400);

  /* Spacing Scale (Tailwind-inspired) */
  --spacing-0: 0;
  --spacing-1: 0.25rem;   /* 4px */
  --spacing-2: 0.5rem;    /* 8px */
  --spacing-3: 0.75rem;   /* 12px */
  --spacing-4: 1rem;      /* 16px */
  --spacing-5: 1.25rem;   /* 20px */
  --spacing-6: 1.5rem;    /* 24px */
  --spacing-8: 2rem;      /* 32px */
  --spacing-10: 2.5rem;   /* 40px */
  --spacing-12: 3rem;     /* 48px */

  /* Typography Scale */
  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;    /* 24px */
  --font-size-3xl: 1.875rem;  /* 30px */

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Border Radius - Subtle medieval feel */
  --radius-sm: 0.25rem;  /* 4px */
  --radius-md: 0.375rem; /* 6px */
  --radius-lg: 0.5rem;   /* 8px */

  /* Shadows - Subtle depth */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* Z-Index Scale */
  --z-dropdown: 1000;
  --z-modal: 2000;
  --z-toast: 3000;
}

/* Dark theme adjustments (future-proof) */
@media (prefers-color-scheme: light) {
  :root {
    --color-bg-primary: var(--color-parchment-50);
    --color-text-primary: var(--color-stone-900);
  }
}
```

### 🟡 Inconsistent macOS-like Styling

**Current State**: Mix of dark terminal aesthetic + basic buttons

**Goal**: Modern macOS-like + D&D fantasy aesthetic

**Reference**: macOS Big Sur/Monterey UI patterns:
- Translucent backgrounds with backdrop blur
- Subtle shadows and depth
- Rounded corners (consistent radius)
- System font stack
- Subtle animations (ease-in-out)

**Proposed Visual Direction**:
```css
/* macOS-inspired panel with D&D theming */
.panel {
  background: linear-gradient(
    135deg,
    rgba(42, 37, 32, 0.95),
    rgba(26, 26, 26, 0.95)
  );
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* macOS-style buttons with fantasy accent */
.btn--primary {
  background: linear-gradient(
    135deg,
    var(--color-arcane-600),
    var(--color-arcane-700)
  );
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.15s ease-out;
}

.btn--primary:hover {
  transform: translateY(-1px);
  box-shadow:
    0 4px 12px rgba(79, 70, 229, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.btn--primary:active {
  transform: translateY(0);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

---

## 6. Clean Architecture Assessment

### ✅ Current Layering (Good)

```
Presentation Layer
  ├── Screens (routing, coordination)
  ├── Components (UI, lifecycle)
  └── Utils (DOM helpers)

Application Layer
  ├── StateStore (app state)
  └── Container (DI)

Infrastructure Layer
  ├── ApiService (HTTP)
  ├── SseService (WebSocket)
  └── Generated Types (backend contract)
```

### ⚠️ Violations

1. **Business logic leaking into screens**:
   - `GameInterfaceScreen.ts:294-340` - Complex tool result formatting should be in a service
   - `ChroniclePanel.ts:252-346` - Entry aggregation logic should be in a service

2. **Missing domain layer**:
   - No models for UI-specific concerns (e.g., `StreamingMessage`, `ChatDisplayState`)
   - Over-reliance on backend types for UI state

**Fix**: Extract domain services:
```typescript
// src/services/domain/ToolResultFormatter.ts
export class ToolResultFormatter {
  formatResult(toolName: string, result: unknown): string {
    if (this.isLevelUpResult(result)) {
      return this.formatLevelUp(result);
    }
    if (this.isRollDiceResult(result)) {
      return this.formatDiceRoll(result);
    }
    return this.formatGeneric(toolName, result);
  }

  private formatLevelUp(result: LevelUpResult): string {
    return `⬆️ Level Up: ${result.old_level} → ${result.new_level} (HP +${result.hp_increase})`;
  }

  private formatDiceRoll(result: RollDiceResult): string {
    const { total, rolls, modifier, roll_type } = result;
    const rollsStr = rolls.length > 0 ? `[${rolls.join(', ')}]` : '';
    const modStr = modifier !== 0 ? (modifier > 0 ? `+${modifier}` : `${modifier}`) : '';
    return `📊 ${roll_type}: ${result.dice}${modStr} = ${total} ${rollsStr}`;
  }
}
```

---

## 7. Actionable Recommendations

### Phase 1: Critical Fixes (1-2 weeks)

#### 1.1 Break Down main.css
- [ ] Split into 15-20 component-scoped CSS files (< 200 lines each)
- [ ] Extract design tokens to `variables.css`
- [ ] Set up Vite to bundle CSS modules
- [ ] Create style guide documentation

**Acceptance Criteria**: No CSS file > 500 lines

#### 1.2 Refactor GameInterfaceScreen
- [ ] Extract `LeftPanelCoordinator` (location + combat + chronicle)
- [ ] Extract `RightPanelCoordinator` (party + character sheet + inventory)
- [ ] Extract `SseEventHandlers` service
- [ ] Screen should be < 300 lines

**Acceptance Criteria**: GameInterfaceScreen.ts < 300 lines, no method > 100 lines

#### 1.3 Refactor ChroniclePanel
- [ ] Extract `ChronicleAggregator` service (handles memory aggregation logic)
- [ ] Extract `ChronicleFilterService` (handles filtering/search logic)
- [ ] Component should only handle UI lifecycle

**Acceptance Criteria**: ChroniclePanel.ts < 300 lines

### Phase 2: Design System (1 week)

#### 2.1 Establish Design Tokens
- [ ] Create comprehensive CSS variables (colors, spacing, typography, shadows)
- [ ] Define D&D-themed color palette (parchment, stone, ember, arcane, nature)
- [ ] Document usage guidelines in `DESIGN_SYSTEM.md`

#### 2.2 Component Library
- [ ] Extract reusable UI builders (`createHeader`, `createSection`, `createCard`)
- [ ] Create `Button` component with variants (primary, secondary, danger)
- [ ] Create `Input` component with validation states
- [ ] Create `Panel` component with consistent styling

#### 2.3 Visual Consistency
- [ ] Apply macOS-inspired styling (translucent panels, subtle shadows, consistent radius)
- [ ] Implement D&D fantasy theming (parchment tones, medieval accents)
- [ ] Add micro-interactions (hover states, active states, focus rings)

### Phase 3: Testing Infrastructure (1 week)

#### 3.1 Component Testing
- [ ] Set up Vitest + Testing Library for components
- [ ] Write tests for base `Component` class
- [ ] Test all lifecycle hooks (mount, update, unmount)
- [ ] Test subscription cleanup

#### 3.2 UI Integration Tests
- [ ] Test screen navigation (ScreenManager)
- [ ] Test panel switching logic
- [ ] Test chat message rendering
- [ ] Test SSE event handling (mock EventSource)

#### 3.3 Visual Regression Testing
- [ ] Set up Playwright + Percy/Chromatic
- [ ] Capture baselines for all screens
- [ ] Add to CI pipeline

### Phase 4: Code Quality (Ongoing)

#### 4.1 Linting & Formatting
- [ ] Configure ESLint rules:
  - Max file lines: 500
  - Max function lines: 100
  - Max cyclomatic complexity: 10
- [ ] Set up pre-commit hooks (lint-staged + husky)

#### 4.2 Documentation
- [ ] Document component architecture in `docs/ARCHITECTURE.md`
- [ ] Add JSDoc comments to all public APIs
- [ ] Create component usage examples

#### 4.3 Performance
- [ ] Profile re-renders (Chrome DevTools)
- [ ] Memoize expensive computations
- [ ] Virtual scrolling for long lists (chronicle, combat log)

---

## 8. Code Examples

### Example 1: Refactored SseEventHandlers

**Before** (GameInterfaceScreen.ts):
```typescript
// 298 lines of inline handlers
private setupSseEventHandlers(container: ServiceContainer, gameId: string): void {
  container.sseService.on('connected', (event) => { /* ... */ });
  container.sseService.on('initial_narrative', (event) => { /* ... 40 lines */ });
  container.sseService.on('narrative', (event) => { /* ... */ });
  // ... 12 more handlers
}
```

**After**:
```typescript
// src/screens/game/SseEventHandlers.ts (150 lines)
export class SseEventHandlers {
  constructor(
    private chatPanel: ChatPanel,
    private stateStore: StateStore,
    private gameId: string,
    private toolFormatter: ToolResultFormatter
  ) {}

  registerAll(sseService: SseService): void {
    sseService.on('connected', this.handleConnected);
    sseService.on('initial_narrative', this.handleInitialNarrative);
    sseService.on('narrative', this.handleNarrative);
    sseService.on('narrative_chunk', this.handleNarrativeChunk);
    sseService.on('tool_call', this.handleToolCall);
    sseService.on('tool_result', this.handleToolResult);
    // ... rest of handlers
  }

  private handleToolResult = (event: TypedSseEvent<'tool_result'>): void => {
    const formatted = this.toolFormatter.formatResult(
      event.data.tool_name,
      event.data.result
    );

    this.chatPanel.addRealtimeMessage({
      type: 'tool-result',
      content: formatted,
      timestamp: event.data.timestamp,
      metadata: {
        toolName: event.data.tool_name,
        result: event.data.result,
      },
    });
  };
}

// GameInterfaceScreen.ts (now 350 lines)
private setupSseEventHandlers(container: ServiceContainer): void {
  const handlers = new SseEventHandlers(
    this.chatPanel!,
    container.stateStore,
    this.props.gameId,
    new ToolResultFormatter()
  );

  handlers.registerAll(container.sseService);
}
```

### Example 2: Design Token Usage

**Before** (main.css):
```css
.chat-panel__header {
  padding: 8px 16px;
  background-color: #3a3a3a;
  border-bottom: 1px solid #404040;
}

.btn--primary {
  padding: 8px 16px;
  background-color: #4a9eff;
  color: #e0e0e0;
  font-size: 13px;
}
```

**After** (with design tokens):
```css
/* styles/components/chat-panel.css */
.chat-panel__header {
  padding: var(--spacing-2) var(--spacing-4);
  background-color: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}

/* styles/components/button.css */
.btn--primary {
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-arcane-gradient);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-md);
  transition: all 0.15s ease-out;
  box-shadow: var(--shadow-sm);
}

.btn--primary:hover {
  background: var(--color-arcane-gradient-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
```

---

## 9. Long-Term Vision

### Ideal Architecture (6-12 months)

```
frontend-v2/
├── src/
│   ├── components/
│   │   ├── base/
│   │   │   ├── Component.ts           (< 150 lines)
│   │   │   ├── Button.ts              (< 100 lines)
│   │   │   ├── Input.ts               (< 100 lines)
│   │   │   └── Panel.ts               (< 150 lines)
│   │   ├── chat/
│   │   │   ├── ChatPanel.ts           (< 200 lines)
│   │   │   ├── ChatPanel.module.css   (< 150 lines)
│   │   │   └── __tests__/ChatPanel.test.ts
│   │   └── ... (each component < 300 lines)
│   ├── services/
│   │   ├── domain/
│   │   │   ├── ToolResultFormatter.ts
│   │   │   ├── ChronicleAggregator.ts
│   │   │   └── StreamingMessageService.ts
│   │   └── ... (existing services)
│   ├── screens/
│   │   ├── game/
│   │   │   ├── GameInterfaceScreen.ts (< 300 lines)
│   │   │   ├── SseEventHandlers.ts
│   │   │   ├── LeftPanelCoordinator.ts
│   │   │   └── RightPanelCoordinator.ts
│   │   └── ... (each screen < 400 lines)
│   └── utils/
│       ├── ui-builders.ts
│       └── __tests__/ui-builders.test.ts
├── styles/
│   ├── core/
│   │   ├── reset.css                  (< 50 lines)
│   │   ├── variables.css              (< 200 lines)
│   │   └── utilities.css              (< 100 lines)
│   ├── components/                    (CSS modules)
│   │   ├── ChatPanel.module.css       (< 150 lines)
│   │   ├── PartyPanel.module.css      (< 150 lines)
│   │   └── ... (each < 200 lines)
│   └── main.css                       (< 50 lines - imports only)
└── docs/
    ├── ARCHITECTURE.md
    ├── DESIGN_SYSTEM.md
    └── COMPONENT_GUIDE.md
```

### Key Metrics (Target State)

| Metric | Current | Target |
|--------|---------|--------|
| Largest file (TS) | 684 lines | < 500 lines |
| Largest file (CSS) | 3,491 lines | < 200 lines |
| Test coverage (services) | ~60% | > 80% |
| Test coverage (components) | 0% | > 70% |
| Longest method | 298 lines | < 100 lines |
| CSS color tokens | ~10 | ~40 (full palette) |
| Component files with tests | 0 | All (30+) |

---

## 10. Conclusion

The frontend-v2 codebase demonstrates **strong architectural foundations** but requires **immediate attention** to file/method sizes, CSS organization, and testing.

**Priority Order**:
1. **Critical** (Blocking): Break down main.css (3,491 → ~500 lines split across files)
2. **Critical** (Blocking): Refactor GameInterfaceScreen (684 → ~300 lines)
3. **High**: Establish design token system (enables consistent styling)
4. **High**: Add component tests (prevents regressions)
5. **Medium**: Refactor ChroniclePanel and extract services
6. **Medium**: macOS-style visual improvements

**Estimated Effort**:
- Phase 1 (Critical Fixes): **2 weeks** (1 developer)
- Phase 2 (Design System): **1 week** (1 designer + 1 developer)
- Phase 3 (Testing): **1 week** (1 developer)
- **Total**: ~4 weeks for production-ready state

**Next Steps**:
1. Review and approve this document
2. Create GitHub issues for each Phase 1 task
3. Assign ownership and set deadlines
4. Begin with CSS splitting (highest ROI, least risky)

---

**Reviewed by**: Claude Code
**Status**: Ready for team review
**Last updated**: 2025-11-08
