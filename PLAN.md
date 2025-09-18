# Dynamic Memory System — Implementation Plan

This plan implements dynamic memories for locations, NPCs, and the world, aligned with SOLID, DRY, and fail‑fast principles. It centralizes a MemoryEntry model, triggers creation on key events, stores memories alongside runtime state, and exposes them via context builders for the narrative agent.

## Goals
- Persist short, useful summaries of what happened at a location visit, with NPCs, and at the world level.
- Save location memories on leaving a location; create NPC memories for present and mentioned NPCs; create world memories on major story state updates.
- Use recent memories in the narrative agent’s prompt context (last 3 per scope, configurable), using recency only.
- Avoid double summarization via per‑scope conversation cursors.
- No UI exposure yet; pure prompt context.

## Data Model

- New: `app/models/memory.py`
  - `MemorySource` enum: `location`, `npc`, `world`.
  - `MemoryEntry` model:
    - `created_at: datetime`
    - `source: MemorySource`
    - `summary: str`
    - `tags: list[str] = []`
    - `location_id: str | None = None`
    - `npc_ids: list[str] = []`
    - `quest_id: str | None = None`
    - `encounter_id: str | None = None`
    - `since_timestamp: datetime | None = None`
    - `since_message_index: int | None = None`
    - Note: No hard requirement for a separate `id` for now; entries are append‑only and ordered.

- Update: `app/models/location.py` (LocationState)
  - Replace `notes: list[str]` with `location_memories: list[MemoryEntry] = []`

- Update: `app/models/instances/npc_instance.py` (NPCInstance)
  - Replace `notes: list[str]` with `npc_memories: list[MemoryEntry] = []`

- Update: `app/models/instances/scenario_instance.py` (ScenarioInstance)
  - Add: `world_memories: list[MemoryEntry] = []`
  - Add per‑scope cursors to avoid double summarization:
    - `last_world_message_index: int = -1`
    - `last_location_message_index: dict[str, int] = {}`  (key: `location_id`)
    - `last_npc_message_index: dict[str, int] = {}`       (key: `npc_instance_id`)
  - Keep `tags`; remove legacy `notes` fields.

## Service Layer

- New interface: `app/interfaces/services/memory.py`
  - `IMemoryService` with responsibilities:
    - `on_location_exit(game_state: GameState) -> None`
      - Creates one Location memory and NPC memories for present+mentioned NPCs.
    - `on_world_event(game_state: GameState, event_kind: str, tags: list[str] | None = None, related: dict[str, str | list[str]] | None = None) -> None`
      - Creates a World memory when story state changes.
    - `prune(game_state: GameState) -> None` (no‑op for now, hook for future pruning).

- New implementation: `app/services/game/memory_service.py`
  - Dependencies: `SummarizerAgent` (for summaries), optionally a logger.
  - Shared helpers (private):
    - `_select_messages_since_index(game_state, since_idx, *, location=None, npc_name=None, include_context_window=False)`
      - Filters `conversation_history` by index and optional metadata (`Message.location`, `Message.npcs_mentioned`).
      - If `include_context_window`, includes one message before and after the mention for extra context.
    - `_record_entry(...)` to append a `MemoryEntry` into target list and update tags.
    - `_update_cursor(...)` to set appropriate last message indices.
  - `on_location_exit` flow (fail‑fast if no current location):
    1) Resolve `from_location_id` from `scenario_instance.current_location_id`; resolve `from_location_name` from scenario sheet (or use `game_state.location`).
    2) Get `since_idx = scenario_instance.last_location_message_index.get(from_location_id, -1)`.
    3) Select messages with `idx > since_idx` and `msg.location == from_location_name`.
    4) If none, return early (no memory to record).
    5) Ask `SummarizerAgent.summarize_location_session(game_state, from_location_id, messages)` for a 2–3 sentence summary.
    6) If empty/failure: log a warning and return (no fallback per requirements).
    7) Create `MemoryEntry` with tags like `['session', f'location:{from_location_id}']`; set `since_message_index` to max idx, `since_timestamp` to first selected message ts.
    8) Append to `LocationState.location_memories` and update cursor `last_location_message_index[from_location_id]`.
    9) For each NPC with `npc.current_location_id == from_location_id` and whose name appears in selected messages:
       - Build a filtered message window (include context window around mentions).
       - Summarize with `SummarizerAgent.summarize_npc_interactions(game_state, npc, messages)`.
       - If summary present, append to `npc.npc_memories` (tags e.g. `['npc-session', f'location:{from_location_id}', f'npc:{npc.instance_id}']`) and update `last_npc_message_index[npc.instance_id]` to max idx considered.
  - `on_world_event` flow:
    1) Determine `since_idx = scenario_instance.last_world_message_index`.
    2) Select `idx > since_idx` (no additional metadata filtering for maximum context), possibly cap the window if ever needed.
    3) If none, return early.
    4) Summarize with `SummarizerAgent.summarize_world_update(game_state, event_kind, messages, related)`.
    5) If summary present, append to `world_memories` with tags `[f'world:{event_kind}', *tags]` and related IDs (`quest_id`, `encounter_id`, etc., from `related`). Update `last_world_message_index`.

## Summarizer Agent Extensions

- Update: `app/agents/summarizer/agent.py`
  - Add methods:
    - `summarize_location_session(game_state, location_id, messages) -> str`
      - Prompt: Summarize notable events in this location during the visit in 2–3 sentences. Focus on outcomes and changes.
    - `summarize_npc_interactions(game_state, npc_instance, messages) -> str`
      - Prompt: Summarize interactions with NPC [name] in 2–3 sentences. Focus on relationships, promises, conflicts, and outcomes.
    - `summarize_world_update(game_state, event_kind, messages, related) -> str`
      - Prompt: Summarize major story progression ([event_kind]) since last world update in 2–3 sentences. Focus on quest/act/encounter outcomes and implications.
  - Behavior: Up to 2 attempts per summary (reuse `_summarize_with_retry`), else return empty; callers log and skip.

## Triggers and Integration Points

- Location exit (save location/NPC memories):
  - Update: `app/events/handlers/location_handler.py`
    - In `ChangeLocationCommand` handling, BEFORE calling `location_service.move_entity(...)`, call `memory_service.on_location_exit(game_state)`.
    - Keep fail‑fast checks (e.g., empty location ID) before memory call.

- World memory triggers:
  - Update: `app/events/handlers/quest_handler.py`
    - After successful mutations, call `memory_service.on_world_event(...)` with:
      - `event_kind='objective_completed'`, related `{ 'quest_id': ..., 'objective_id': ... }` (CompleteObjective)
      - `event_kind='quest_completed'`, related `{ 'quest_id': ... }` (CompleteQuest)
      - `event_kind='act_progressed'`, related `{ 'act_id': ... }` (ProgressAct)
  - Update: `app/events/handlers/location_handler.py` (UpdateLocationStateCommand)
    - If `danger_level == 'CLEARED'`: call `on_world_event(..., event_kind='location_cleared', related={'location_id': ...})`.
    - If `complete_encounter` provided: call `on_world_event(..., event_kind='encounter_completed', related={'location_id': ..., 'encounter_id': ...})`.

## Prompt Context

- New builders under `app/services/ai/context_builders/`:
  - `location_memory_builder.py` — “Recent Location Memory”
    - Include last N (default 3) `LocationState.location_memories` for current location.
  - `npc_memory_builder.py` — “NPC Memory”
    - For each NPC present at current location, include last N (default 3) `npc_memories`.
  - `world_memory_builder.py` — “World Memory”
    - Include last N (default 3) `ScenarioInstance.world_memories`.
  - Builders produce concise, single‑line bullets per entry (date + short summary), no heavy formatting.

- Update: `app/services/ai/context_service.py`
  - Add these builders only to Narrative agent’s selected builders.
  - Keep count limits configurable via optional constructor params or class attributes (for now, constants in builders: `MAX_ENTRIES = 3`).

## Container and Wiring

- New: `container.memory_service` (cached_property)
  - Instantiate `MemoryService` with `summarizer_agent` (or inject a summarizer proxy via orchestrator dependencies if circular import concerns arise; simplest: have `MemoryService` accept `SummarizerAgent` via container after agents are constructed).
  - Register in handlers:
    - `LocationHandler(self.location_service, self.memory_service)`
    - `QuestHandler(self.memory_service)`

Note on ordering: If circular init arises (SummarizerAgent requires ContextService; MemoryService requires SummarizerAgent), construct `SummarizerAgent` first, then `MemoryService`, then EventBus/handlers.

## Persistence

- No changes to `SaveManager` structure required. The new fields live within `ScenarioInstance`, `LocationState`, and `NPCInstance` which are already serialized independently.
- `PreSaveSanitizer` remains focused on entity cleanup (no changes).

## Failure Handling
- If no messages found after the last cursor for a scope, skip memory creation (fast‑fail, no‑op).
- If summarization fails or returns empty, log a warning and skip adding memory (no fallback content).
- All handlers maintain their original error paths (e.g., invalid IDs) before invoking memory hooks.

## Pruning (Extensible, No‑Op Now)
- `IMemoryService.prune(game_state)` reserved for future pruning policies (max entries per scope, tag‑based pruning). For now, it’s a no‑op to satisfy requirement without altering behavior.

## Compatibility
- This is a full transition. Legacy `notes` fields are removed and replaced by structured memory fields.

## Test Plan

Unit tests (new):
- `test_memory_service_location_exit_creates_entries_and_updates_cursors`
  - Given conversation history at a location, `on_location_exit` adds one `LocationState.location_memories` entry and updates `last_location_message_index`.
- `test_memory_service_npc_entries_only_for_present_and_mentioned`
  - Given present NPCs, only those mentioned produce `npc_memories` entries.
- `test_memory_service_world_event_creates_world_memory`
  - After `on_world_event('quest_completed', ...)`, adds one `world_memories` entry and updates `last_world_message_index`.

Handler integration (adapt existing tests with mocks):
- Update `tests/unit/events/handlers/test_location_handler.py` to pass a mocked `IMemoryService` to `LocationHandler` and assert:
  - `on_location_exit` is called in `ChangeLocationCommand`.
  - `on_world_event` called when `danger_level='CLEARED'` or `complete_encounter` provided.
- Update `tests/unit/events/handlers/test_quest_handler.py` to construct `QuestHandler(memory_service=mock)` and assert `on_world_event` call on each relevant command.

## Step‑By‑Step Implementation

1) Models
   - Add `app/models/memory.py`.
   - Replace legacy `notes` fields in `LocationState` and `NPCInstance` with structured memory fields.
   - Add `world_memories` and cursors to `ScenarioInstance` and remove any legacy `notes` there if present.

2) Interfaces and Service
   - Add `app/interfaces/services/memory.py` (`IMemoryService`).
   - Implement `app/services/game/memory_service.py` with selection, summarization, recording, and cursor updates.

3) SummarizerAgent
   - Add the three summarization methods with clear, minimal prompts; reuse retry helper.

4) Handlers
   - Modify `LocationHandler` and `QuestHandler` constructors to accept `IMemoryService`.
   - Insert calls as described under Triggers.

5) Context Builders
   - Add memory builders and wire them into `ContextService` for the Narrative agent.

6) Container
   - Instantiate `MemoryService` and inject into handlers.

7) Tests
   - Update handler tests to pass a mock memory service and assert calls.
   - Add unit tests for `MemoryService` core behavior.

8) Documentation
   - Keep this PLAN.md updated; optional: add brief docstrings on new methods.

## Configuration
- Default memory inclusion limits: 3 entries per scope in builders.
- Future: make limits configurable via settings if needed.

## Non‑Goals (Now)
- UI exposure of memories.
- Automatic migration of legacy `notes` content.
- Memory pruning beyond the no‑op hook.
