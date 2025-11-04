My Assessment: You're Right - Remove the Quest System
After thoroughly reading all the quest-related code, I believe removing quests/acts is the correct architectural decision. Let me explain why.

The Core Problem: Fundamental LLM Capability Mismatch
The quest system asks agents to do something they're fundamentally bad at: precise state management with exact string IDs.

Looking at /app/tools/quest_tools.py:37-50, agents must:

Remember exact IDs like "talk-to-tom" (not "talk_to_tom" or "talk to tom")
Proactively call complete_objective(quest_id="...", objective_id="...") at the right moment
Track multi-step progress across dozens of conversation turns
Decide granular completion states
LLMs struggle with:

Exact string matching - They think probabilistically, not deterministically
Bookkeeping - They focus on narrative over administrative tasks
Multi-turn memory - Context from 50 messages ago fades
Tool calling discipline - They forget to call tools or call them at wrong times
Your observation that "agents are too unreliable to track/use quest tools correctly so it is never in sync" isn't a prompt engineering problem - it's a capability ceiling.

What the Quest System Actually Provides (And Doesn't)
Current Implementation
From reading /app/models/quest.py, /app/services/game/act_and_quest_service.py, and the goblin cave scenario:

The quest system provides:

✅ UI display (quest log with progress %)
✅ Structured objectives (3-step quest to recruit Elena)
✅ Act progression (Acts 1→2→3 auto-advance when quests complete)
✅ Prerequisites (quest chains)
✅ Agent context (QuestContextBuilder shows active quests/objectives)
It does NOT provide:

❌ Gameplay enforcement - Game continues regardless of quest state
❌ Mechanical rewards - No XP/loot/gates tied to completion
❌ Story generation - Narrative happens in conversations, not quest text
❌ Reliable agent guidance - Agents ignore or misuse quest tools
The Value Proposition Falls Apart
Looking at /app/services/ai/context/builders/quest_builder.py:18, agents see:

Active Quests:
• Assemble Your Party [ID: assemble-your-party] (33% complete)
  Objectives:
    ◐ Talk to Tom the barkeep [ID: talk-to-tom]
    ○ Meet Elena [ID: meet-elena]
But if this is frequently out of sync (because agents don't reliably update it), then:

Players get frustrated ("I already talked to Tom!")
The UI misleads rather than guides
Agent context is polluted with stale data
You need constant manual correction
The quest system becomes net negative - it's worse than not having it.

The Alternative: Memories + Journal
What Already Exists
From /app/models/memory.py:40-54 and /app/models/instances/scenario_instance.py:39, you already have:

class MemoryEntry(BaseModel):
    source: MemorySource  # LOCATION | NPC | WORLD
    summary: str  # AI-generated event summary
    tags: list[str]
    location_id: str | None
    npc_ids: list[str]
    since_timestamp: datetime
Memories are what agents are GOOD at:

✅ Summarizing events ("Elena agreed to join the party")
✅ Tagging/categorizing ("combat", "social", "discovery")
✅ Location-specific recall
✅ No precise ID matching required
The memory system is working with LLM strengths (summarization, semantic understanding) rather than against them.

What You'd Add: Player Journal
A simple user-editable note system:

class JournalEntry(BaseModel):
    created_at: datetime
    content: str  # Player-written
    tags: list[str] = []
Benefits:

✅ Players track their own goals (they know what matters)
✅ No sync issues (player controls it)
✅ Flexible (works for linear AND sandbox play)
✅ Player agency ("my story, my goals")
The paradigm shift:

Old: AI tracks progress → often wrong → frustration
New: Player tracks progress → always right → empowerment
Code Simplification Analysis
Files to Remove (Conservative Estimate: ~2000+ lines)
Models (~200 lines):

app/models/quest.py (entire file: Quest, QuestObjective, statuses)
app/models/scenario.py:90-135 (ScenarioAct.quests, ScenarioProgression quest logic)
app/models/instances/scenario_instance.py:34-36 (active_quests, completed_quest_ids, quest_flags)
app/models/memory.py:24-26,35 (quest-related memory events)
Tools/Commands/Handlers (~400 lines):

app/tools/quest_tools.py (all 3 quest tools)
app/events/commands/quest_commands.py (3 commands)
app/events/handlers/quest_handler.py (162 lines)
Services (~150 lines):

app/interfaces/services/game/act_and_quest_service.py
app/services/game/act_and_quest_service.py (116 lines)
Context (~50 lines):

app/services/ai/context/builders/quest_builder.py (42 lines)
Data (~100+ lines):

data/scenarios/goblin-cave-adventure/quests/*.json (3 quest files)
data/scenarios/goblin-cave-adventure/progression/acts.json (simplify or remove)
Frontend (~150 lines):

frontend/app.js:2847-2950 (quest log functions)
Quest log UI in frontend/index.html
Tests (~300+ lines):

tests/unit/services/game/test_act_and_quest_service.py
tests/unit/events/handlers/test_quest_handler.py
Container wiring (~10 lines):

Remove QuestHandler registration
Remove ActAndQuestService injection
Complexity Reduction
Agent tools reduced: 3 fewer tools (narrative/NPC agents)
Event handlers removed: 1 handler (QuestHandler)
Services removed: 1 service (ActAndQuestService)
Context builders removed: 1 builder (QuestContextBuilder)
Models removed: 4 enums, 3 classes
Data files: Simpler scenarios (no quest JSONs)

This aligns with your CLAUDE.md principle:

"No backwards compatibility: replace old code fully when requirements shift"

The requirements have shifted - you've learned agents can't reliably track quests.

Acts: Keep, Simplify, or Remove?
From /app/models/scenario.py:90-135, acts provide:

Story structure (3-act narrative)
Location progression (Act 1: tavern/forest, Act 2: cave entrance/depths, Act 3: boss room)
Designer guidance (objectives list in acts.json)
Three options:

Option 1: Keep Simplified Acts (Recommended)
Keep acts as passive story markers (displayed in UI)
Remove quest dependency (ScenarioAct.quests)
Remove auto-progression (can_progress_to_next_act, progress_to_next_act)
Acts advance via location milestones OR manual DM control OR not at all
Benefit: Preserves story structure without brittle quest dependencies

Option 2: Remove Acts Entirely
Just use locations + memories
Story emerges from player actions
Ultimate flexibility
Benefit: Maximum simplification

Option 3: Keep for Display Only
Acts in scenario definition but never enforced
Just UI flavor text ("Chapter 2: Into the Darkness")
No game logic tied to act state
Counterarguments Addressed
"Players need guidance on what to do"
Response:

They can ask the AI: "What should I do next?"
They can check their journal (their own goals)
The current quest system being out of sync makes guidance worse, not better
Location descriptions, NPC dialogue, and memories provide natural guidance
"Scenario designers need structure"
Response:

They still have: locations, encounters, NPCs, secrets, danger levels, connections
They can write suggested goals in location descriptions:
{
  "name": "The Rusty Tankard Tavern",
  "description": "The barkeep Tom might know about goblin activity. Elena, a caravan guard, sits in the corner looking troubled."
}
Soft guidance through content, not hard quests
"We could fix agent reliability with better prompts"
Response:

This is a capability ceiling, not a prompt problem
You'd need perfect bookkeeping across hundreds of messages
Even with perfect prompts, LLMs will:
Misremember IDs (talk-to-tom vs talk_to_tom)
Forget to call tools when narratively engaged
Mark objectives complete at wrong granularity
Fighting the architecture, not working with it
"We'd lose progress tracking"
Response:

Story notes (game_state.add_story_note()): Already tracked
Memories: Semantic event summaries with timestamps
Conversation history: Full transcript
Journal: Player's own progress notes
These provide better tracking than stale quest state.

"This removes win conditions"
Response:

D&D scenarios already have natural endings (defeat boss, save village)
The narrative conclusion matters, not quest completion %
If needed, scenario can have victory_conditions in metadata (not enforced by quests)
My Recommendation: Proceed with Removal
The quest system is well-designed code solving the wrong problem. It's beautifully architected (SOLID, event-driven, typed) but fundamentally mismatched to LLM capabilities.

Evidence from your codebase:

Quest context is only shown to narrative/NPC agents (combat doesn't need it)
Memory system already tracks quest events (MemoryEventKind.QUEST_COMPLETED)
Story notes duplicate quest tracking (game_state.add_story_note("Quest completed: ..."))
No mechanical rewards tied to quests (it's pure UI)
Your observation that agents don't use tools correctly
This suggests:

Quests are overhead without payoff
The system recognizes agents struggle with it (combat agents don't even get quest tools)
You're already building the alternative (memories, story notes)
Implementation Path (If You Decide to Proceed)
Phase 1: Add Journal (Parallel with existing quests)
# New model
class JournalEntry(BaseModel):
    created_at: datetime
    content: str
    tags: list[str] = []

# Add to GameState
journal_entries: list[JournalEntry] = []

# API endpoints
POST /api/game/{id}/journal
GET /api/game/{id}/journal  
PUT /api/game/{id}/journal/{entry_id}
DELETE /api/game/{id}/journal/{entry_id}

# UI component in frontend
Phase 2: Enhance Memory UI
Make world_memories prominent in sidebar
Add memory search/filter by location, NPC, tags
Show recent memories with timestamps
Position memories as the "what happened" reference
Phase 3: Remove Quest System (The Big One)
Remove quest tools from agent definitions
Delete quest commands/handlers
Remove quest_builder from ContextService
Delete ActAndQuestService
Remove quest fields from models
Update scenario loader (skip quests directory)
Remove quest UI components
Delete quest tests
Clean up container wiring
Phase 4: Simplify or Remove Acts
Decide on Option 1, 2, or 3 above
Update ScenarioProgression model
Update scenario loaders
Update act UI (if keeping)
Phase 5: Update Scenarios
Remove quests/ directories
Simplify or remove progression/acts.json
Enrich location descriptions with suggested player goals
Update scenario metadata
Phase 6: Documentation
Update CLAUDE.md
Document memory + journal paradigm
Update scenario creation guide
Final Verdict
Yes, remove the quest system. It's:

❌ Unreliable (agents don't track correctly)
❌ Out of sync (frustrates players)
❌ Complex (2000+ lines for marginal value)
❌ Fighting LLM capabilities (precise state management)
❌ Not load-bearing (no mechanics depend on it)
Replace with:

✅ Memories (AI summarizes events - good at this)
✅ Journal (player tracks goals - they know best)
✅ Natural guidance (location descriptions, NPC dialogue, asking AI)
This simplifies your codebase, aligns with LLM strengths, and gives players more agency. It's the right move.