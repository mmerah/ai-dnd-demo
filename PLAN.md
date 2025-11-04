# Quest & Act System Removal Plan

## Executive Summary

**Decision**: Remove both the quest system and act system entirely.

**Rationale**:
- Agents are unreliable at tracking quest state (precise ID matching, multi-turn bookkeeping)
- The system is frequently out of sync, frustrating users
- Quests provide no mechanical enforcement or rewards - purely UI overhead
- Acts are tightly coupled to quests and add complexity without value
- Memory + journal system better aligns with LLM strengths (summarization, semantic understanding)

**Estimated Removal**: ~2,500+ lines of code across 30+ files

---

## Phase 1: Backend - Remove Quest System

### 1.1 Remove Quest Models
**Files to delete:**
- [x] `app/models/quest.py` (79 lines - entire file)

**Files to modify:**
- [ ] `app/models/scenario.py`
  - Remove: `from app.models.quest import Quest` (line 7)
  - Remove: `quests: list[Quest] = Field(default_factory=list)` from ScenarioSheet (line 146)
  - Remove: `get_quest()` method (lines 167-172)

- [ ] `app/models/instances/scenario_instance.py`
  - Remove: `from app.models.quest import Quest` (line 12)
  - Remove: `active_quests: list[Quest] = Field(default_factory=list)` (line 34)
  - Remove: `completed_quest_ids: list[str] = Field(default_factory=list)` (line 35)
  - Remove: `quest_flags: dict[str, JSONSerializable] = Field(default_factory=dict)` (line 36)

- [ ] `app/models/memory.py`
  - Remove: `OBJECTIVE_COMPLETED = "objective_completed"` from MemoryEventKind (line 24)
  - Remove: `QUEST_COMPLETED = "quest_completed"` from MemoryEventKind (line 25)
  - Remove: `quest_id: str | None = None` from MemoryEntry (line 49)
  - Remove: `objective_id: str | None = None` from MemoryEntry (line 51)
  - Remove: `quest_id: str | None = None` from WorldEventContext (line 33)
  - Remove: `objective_id: str | None = None` from WorldEventContext (line 35)

### 1.2 Remove Quest Tools
**Files to delete:**
- [x] `app/tools/quest_tools.py` (68 lines - entire file)

**Files to modify:**
- [ ] `app/agents/narrative/agent.py`
  - Remove: `quest_tools,` from imports (line 40)
  - Remove: All registrations of quest tools in `get_tools()` method

- [ ] `app/agents/npc/base.py`
  - Remove: `quest_tools` from imports (line 40)
  - Remove: All registrations of quest tools in `get_tools()` method

### 1.3 Remove Quest Commands
**Files to delete:**
- [x] `app/events/commands/quest_commands.py` (41 lines - entire file)

### 1.4 Remove Quest Handler
**Files to delete:**
- [x] `app/events/handlers/quest_handler.py` (162 lines - entire file)

**Files to modify:**
- [ ] `app/container.py`
  - Remove: `from app.events.handlers.quest_handler import QuestHandler` (line 18)
  - Remove: Quest handler registration in `event_bus` property (line 450)

### 1.5 Remove Quest Service
**Files to delete:**
- [x] `app/services/game/act_and_quest_service.py` (116 lines - entire file)
- [x] `app/interfaces/services/game/act_and_quest_service.py` (81 lines - entire file)

**Files to modify:**
- [ ] `app/container.py`
  - Remove: `from app.services.game.act_and_quest_service import ActAndQuestService` (line 105)
  - Remove: `from app.interfaces.services.game import IActAndQuestService` (line 45)
  - Remove: `act_and_quest_service` property (lines 256-257)
  - Remove: `act_and_quest_service=self.act_and_quest_service` from GameFactory init (line 141)

- [ ] `app/interfaces/services/game/__init__.py`
  - Remove: `IActAndQuestService` export

- [ ] `app/services/game/game_factory.py`
  - Remove: `from app.interfaces.services.game import IActAndQuestService` (line 7)
  - Remove: `act_and_quest_service: IActAndQuestService` parameter from __init__ (line 32)
  - Remove: `self.act_and_quest_service = act_and_quest_service` (line 46)
  - Remove: Quest initialization block in `initialize_game()` (lines 164-173)

### 1.6 Remove Quest Context Builder
**Files to delete:**
- [x] `app/services/ai/context/builders/quest_builder.py` (42 lines - entire file)

**Files to modify:**
- [ ] `app/services/ai/context/composition.py`
  - Remove: `from app.services.ai.context.builders.quest_builder import QuestContextBuilder` (line 23)
  - Remove: `quests: QuestContextBuilder` from BuilderRegistry (line 50)

- [ ] `app/services/ai/context/context_service.py`
  - Remove: Quest builder instantiation
  - Remove: `.add(builders.quests)` from all agent compositions

- [ ] `app/services/ai/context/builders/__init__.py`
  - Remove: Any exports of QuestContextBuilder

### 1.7 Remove Quest Tool Results
**Files to modify:**
- [ ] `app/models/tool_results.py`
  - Remove: `StartQuestResult` class (lines 95-101)
  - Remove: `CompleteObjectiveResult` class (lines 103-110)
  - Remove: `CompleteQuestResult` class (lines 112-118)
  - Remove: These types from `ToolResult` union (lines 262-264)

### 1.8 Update Scenario Loader
**Files to modify:**
- [ ] `app/services/data/loaders/scenario_loader.py`
  - Remove: `from app.models.quest import ObjectiveStatus, Quest, QuestObjective, QuestStatus` (line 11)
  - Remove: `quests = self._load_quests(scenario_dir, data.get("quests", []))` (line 53)
  - Remove: `quests=quests,` from ScenarioSheet init (line 63)
  - Remove: `_load_quests()` method (lines 297-322)
  - Remove: `_load_quest_file()` method (lines 324-357)

---

## Phase 2: Backend - Remove Act System

### 2.1 Remove Act Models
**Files to modify:**
- [ ] `app/models/scenario.py`
  - Remove: `ScenarioAct` class (lines 90-98)
  - Remove: `ScenarioProgression` class (lines 100-135)
  - Remove: `progression: ScenarioProgression` from ScenarioSheet (line 147)
  - Consider: Keep simplified progression metadata for UI flavor (optional "chapter" string)

- [ ] `app/models/instances/scenario_instance.py`
  - Remove: `current_act_id: str` field (line 30)
  - Note: This may break initialization - handle in GameFactory

- [ ] `app/models/memory.py`
  - Remove: `ACT_PROGRESSED = "act_progressed"` from MemoryEventKind (line 26)
  - Remove: `act_id: str | None = None` from MemoryEntry (line 52)
  - Remove: `act_id: str | None = None` from WorldEventContext (line 36)

### 2.2 Update Scenario Loader
**Files to modify:**
- [ ] `app/services/data/loaders/scenario_loader.py`
  - Remove: `from app.models.scenario import ScenarioAct, ScenarioProgression` (lines 15-18)
  - Remove: `progression = self._load_progression(scenario_dir, data.get("progression", "acts"))` (line 54)
  - Remove: `progression=progression if progression else ScenarioProgression(acts=[]),` from ScenarioSheet (line 64)
  - Remove: `_load_progression()` method (lines 359-401)

### 2.3 Update Game Factory
**Files to modify:**
- [ ] `app/services/game/game_factory.py`
  - Remove: Act initialization logic in `initialize_game()`:
    - `current_act_id=scenario.progression.acts[0].id` (line 111)
  - Handle ScenarioInstance creation without `current_act_id`

---

## Phase 3: Data - Remove Quest & Act Content

### 3.1 Delete Quest JSON Files
**Files to delete:**
- [x] `data/scenarios/goblin-cave-adventure/quests/assemble-your-party.json`
- [x] `data/scenarios/goblin-cave-adventure/quests/clear-goblin-cave.json`
- [x] `data/scenarios/goblin-cave-adventure/quests/defeat-the-goblin-boss.json`
- [x] `data/scenarios/goblin-cave-adventure/quests/` (directory)

### 3.2 Delete/Simplify Act Progression Files
**Files to delete:**
- [x] `data/scenarios/goblin-cave-adventure/progression/acts.json`
- [x] `data/scenarios/goblin-cave-adventure/progression/` (directory if empty)

### 3.3 Update Scenario Manifest
**Files to modify:**
- [ ] `data/scenarios/goblin-cave-adventure/scenario.json`
  - Remove: `"quests": [...]` array
  - Remove: `"progression": "acts"` field
  - Consider: Add guidance in location descriptions (e.g., "Tom the barkeep might know about goblins")

### 3.4 Enrich Location Descriptions (Optional Enhancement)
**Files to modify:**
- [ ] `data/scenarios/goblin-cave-adventure/locations/tavern.json`
  - Enhance description to naturally guide player: "The barkeep Tom looks troubled. Elena, a caravan guard, sits in the corner."

---

## Phase 4: Frontend - Remove Quest & Act UI

### 4.1 Remove Quest Log UI
**Files to modify:**
- [ ] `frontend/index.html`
  - Remove: Quest log container/section (search for "questLog", "quest-" classes)
  - Remove: Quest count badge if exists

- [ ] `frontend/app.js`
  - Remove: `updateQuestLogFromGameState()` function (lines 2847-2856)
  - Remove: `updateQuestLog()` function (lines 2880-2950)
  - Remove: Quest-related SSE update logic (line 885-887)
  - Remove: `window.previousQuestIds` tracking (line 2949)

- [ ] `frontend/style.css`
  - Remove: All quest-related CSS classes (.quest-item, .quest-header, .objective-list, etc.)

### 4.2 Remove Act UI
**Files to modify:**
- [ ] `frontend/app.js`
  - Remove: `updateActInfoFromGameState()` function (if exists)
  - Remove: `updateActInfo()` function (if exists)
  - Remove: Act-related SSE update logic

- [ ] `frontend/index.html`
  - Remove: Act/chapter display elements

- [ ] `frontend/style.css`
  - Remove: Act-related CSS classes

---

## Phase 5: Tests - Remove Quest & Act Tests

### 5.1 Delete Test Files
**Files to delete:**
- [x] `tests/unit/events/handlers/test_quest_handler.py`
- [x] `tests/unit/services/game/test_act_and_quest_service.py`

### 5.2 Update Test Fixtures
**Files to modify:**
- [ ] `tests/unit/services/game/test_game_factory.py`
  - Remove: Quest/act assertions
  - Update: ScenarioSheet fixtures to not include quests/progression

- [ ] `tests/integration/test_orchestrator_multi_tool_flow.py`
  - Remove: Any quest tool usage
  - Update: Test scenarios

- [ ] Any other test files importing quest models/services

---

## Phase 6: Documentation & Configuration

### 6.1 Update CLAUDE.md
**Files to modify:**
- [ ] `CLAUDE.md`
  - Remove: References to quest system in Structure section
  - Remove: `quest_tools` from tools list (line mentioning quest_tools.py)
  - Remove: Quest handler from events/handlers list
  - Remove: ActAndQuestService from services list
  - Remove: Quest models from models section
  - Update: Flow section to remove quest-related steps
  - Add: Note about memory + journal approach

### 6.2 Update Documentation Files
**Files to modify/create:**
- [ ] `docs/orchestration.md` (if it mentions quests)
- [ ] `docs/context_building.md` (remove quest builder references)
- [ ] Consider: Create `docs/memory_and_journal.md` documenting new approach

### 6.3 Clean Up Configuration
**Files to check:**
- [ ] `.env.example` - No quest-related env vars expected
- [ ] `pyproject.toml` - No changes needed
- [ ] Any agent prompt files that mention quests

---

## Phase 7: Player Journal & Memory Chronicle System (Future Enhancement)

**Note**: This is the replacement system, but should be implemented AFTER quest removal to keep changes atomic.

### 7.1 Create Player Journal Models
**New files:**
- [ ] `app/models/player_journal.py`
  ```python
  class PlayerJournalEntry(BaseModel):
      entry_id: str
      created_at: datetime
      updated_at: datetime
      content: str  # Player-written notes
      tags: list[str] = []
  ```

### 7.2 Add Player Journal to GameState
**Files to modify:**
- [ ] `app/models/game_state.py`
  - Add: `player_journal_entries: list[PlayerJournalEntry] = Field(default_factory=list)`

### 7.3 Create Player Journal API Endpoints
**New files:**
- [ ] `app/api/routers/player_journal.py`
  - POST `/api/game/{game_id}/player-journal` - Create entry
  - GET `/api/game/{game_id}/player-journal` - List entries
  - PUT `/api/game/{game_id}/player-journal/{entry_id}` - Update entry
  - DELETE `/api/game/{game_id}/player-journal/{entry_id}` - Delete entry

### 7.4 Add Unified Chronicle UI
**Concept**: Replace quest log with a "Chronicle" panel that combines:
- **Location Memories** (from `scenario_instance.world_memories` filtered by location)
- **World Memories** (from `scenario_instance.world_memories` - major events)
- **Player Journal** (from `player_journal_entries` - user-editable notes)

**Files to modify:**
- [ ] `frontend/index.html`
  - Replace quest log section with "Chronicle" panel
  - Add tabs/filters: "All", "Location Memories", "World Events", "My Notes"
  - Add "New Note" button for player journal entries
  - Display entries sorted by timestamp (newest first) or filterable by tags

- [ ] `frontend/app.js`
  - Add: `updateChronicleFromGameState()` function
  - Add: Player journal CRUD functions (create/read/update/delete)
  - Add: Memory filtering/sorting logic (by source, location, tags)
  - Add: Tag-based filtering UI

- [ ] `frontend/style.css`
  - Style chronicle panel with tabbed interface
  - Differentiate entry types visually:
    - Location memories: blue/gray badge
    - World events: gold/amber badge
    - Player notes: green badge + edit icon
  - Style tag chips for filtering

**Example Chronicle Entry Display:**
```
┌─────────────────────────────────────────────────┐
│ Chronicle                                       │
├─────────────────────────────────────────────────┤
│ [All] [Locations] [World] [My Notes]           │
├─────────────────────────────────────────────────┤
│ 🌍 Day 1, Hour 14 | World Event                │
│ Elena joined the party to hunt goblins          │
│ Tags: #party #npc:elena                         │
├─────────────────────────────────────────────────┤
│ 📍 Day 1, Hour 12 | The Rusty Tankard           │
│ Spoke with Tom about goblin raids. Learned      │
│ about cave entrance to the north.               │
│ Tags: #location:tavern #npc:tom                 │
├─────────────────────────────────────────────────┤
│ ✏️ Day 1, Hour 15 | My Notes          [Edit]   │
│ Remember to stock up on healing potions before  │
│ entering the cave. Tom mentioned traps.         │
│ Tags: #todo #preparation                        │
└─────────────────────────────────────────────────┘
```

### 7.5 Memory Tag Enhancement (Optional)
**Files to modify:**
- [ ] `app/services/game/memory_service.py`
  - Enhance auto-tagging: Add `#major-event`, `#combat`, `#discovery`, etc.
  - Add location names as tags automatically

---

## Validation Checklist

After completing removal:

### Build & Type Safety
- [ ] `mypy --strict app tests` passes with no errors
- [ ] `ruff check .` passes with no errors
- [ ] `ruff format .` applied successfully

### Tests
- [ ] `pytest` all tests pass
- [ ] No imports of deleted modules remain
- [ ] Integration tests run successfully

### Runtime
- [ ] Application starts without errors
- [ ] Can create new game without crashes
- [ ] Location changes work correctly
- [ ] Memory system functions properly
- [ ] Combat flow unaffected
- [ ] NPCs spawn and interact normally

### Data
- [ ] Scenario loads without quest/act data
- [ ] No broken references in scenario JSON
- [ ] Frontend displays game state correctly

### Code Quality
- [ ] No orphaned imports
- [ ] No dead code or commented-out quest logic
- [ ] All TODOs/FIXMEs addressed or documented
- [ ] CLAUDE.md accurately reflects architecture

---

---

## Notes

1. **Atomicity**: Complete quest removal before starting act removal to isolate issues
2. **Testing**: Run full test suite after each phase
3. **Migration**: No save file migration needed - old saves with quest data will simply ignore those fields (Pydantic drops extra fields by default)
4. **Backward Compatibility**: Intentionally breaking - aligns with CLAUDE.md principle "No backwards compatibility: replace old code fully when requirements shift"
