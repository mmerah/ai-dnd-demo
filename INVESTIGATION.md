# Schema Fix Investigation

## Problem Statement

The `app/api/routers/schemas.py` file contains completely wrong/invented model imports and exports. The schemas being exported don't match the actual backend models, which will cause massive type mismatches in the frontend.

## Investigation Results

### Current (WRONG) schemas.py imports:
```python
from app.models.ai_response import (
    AIStreamChunk,        # ❌ WRONG - doesn't exist
    AICompleteResponse,   # ❌ WRONG - doesn't exist
    AIErrorResponse,      # ❌ WRONG - doesn't exist
)
from app.models.character import Character         # ❌ WRONG - should be CharacterSheet
from app.models.combat import Combat, Combatant, Initiative  # ❌ WRONG - should be CombatState, CombatParticipant, no Initiative
from app.models.damage_types import DamageType    # ❌ WRONG - should be damage_type (singular)
from app.models.location import Location          # ❌ WRONG - should be LocationState
from app.models.npc import NPC                    # ❌ WRONG - should be NPCSheet
from app.models.party import Party                # ❌ WRONG - should be PartyState
from app.models.quest import Quest                # ❌ WRONG - doesn't exist
from app.models.spell import Spell                # ❌ WRONG - should be SpellDefinition
```

### Actual Backend Models (CORRECT):

#### Core Game State Models:
- **app/models/game_state.py**:
  - `GameState` ✅
  - `Message` ✅
  - `GameEvent` ✅
  - `GameTime` ✅
  - `DialogueSessionState` ✅

- **app/models/character.py**:
  - `CharacterSheet` ✅ (NOT "Character")
  - `Currency` ✅
  - `Personality` ✅
  - `CustomFeature` ✅

- **app/models/combat.py**:
  - `CombatState` ✅ (NOT "Combat")
  - `CombatParticipant` ✅ (NOT "Combatant")
  - `CombatSuggestion` ✅
  - `CombatEntry` ✅
  - `MonsterSpawnInfo` ✅
  - NO "Initiative" class exists ❌

- **app/models/location.py**:
  - `LocationState` ✅ (NOT "Location")
  - `LocationConnection` ✅
  - `LootEntry` ✅
  - `EncounterParticipantSpawn` ✅

- **app/models/party.py**:
  - `PartyState` ✅ (NOT "Party")

- **app/models/npc.py**:
  - `NPCSheet` ✅ (NOT "NPC")

- **app/models/memory.py**:
  - `MemoryEntry` ✅
  - `WorldEventContext` ✅

#### Instance Models (Display Snapshots):
- **app/models/instances/character_instance.py**:
  - `CharacterInstance` ✅

- **app/models/instances/monster_instance.py**:
  - `MonsterInstance` ✅

- **app/models/instances/npc_instance.py**:
  - `NPCInstance` ✅

- **app/models/instances/scenario_instance.py**:
  - `ScenarioInstance` ✅

- **app/models/instances/entity_state.py**:
  - `EntityState` ✅
  - `HitPoints` ✅
  - `HitDice` ✅

- **app/models/instances/base_instance.py**:
  - `BaseInstance` ✅

#### AI Response Models:
- **app/models/ai_response.py**:
  - `NarrativeChunkResponse` ✅ (NOT "AIStreamChunk")
  - `CompleteResponse` ✅ (NOT "AICompleteResponse")
  - `ErrorResponse` ✅ (NOT "AIErrorResponse")
  - `NarrativeResponse` ✅
  - `StreamEvent` ✅

#### SSE Event Models:
- **app/models/sse_events.py**:
  - `SSEEvent` ✅
  - `ConnectedData` ✅
  - `HeartbeatData` ✅
  - `NarrativeData` ✅
  - `InitialNarrativeData` ✅
  - `ToolCallData` ✅
  - `ToolResultData` ✅
  - `NPCDialogueData` ✅
  - `CombatUpdateData` ✅
  - `CombatSuggestionData` ✅
  - `SystemMessageData` ✅
  - `ErrorData` ✅
  - `GameUpdateData` ✅
  - `CompleteData` ✅

#### Data Definition Models:
- **app/models/spell.py**:
  - `SpellDefinition` ✅ (NOT "Spell")
  - `SpellSlot` ✅
  - `Spellcasting` ✅

- **app/models/damage_type.py**: (NOT damage_types plural!)
  - `DamageType` ✅

- **app/models/item.py**:
  - `ItemDefinition` ✅
  - `InventoryItem` ✅

- **app/models/monster.py**:
  - `MonsterSheet` ✅

- **app/models/scenario.py**:
  - `ScenarioSheet` ✅
  - `ScenarioLocation` ✅
  - `Encounter` ✅

- **app/models/tool_suggestion.py**:
  - `ToolSuggestion` ✅
  - `ToolSuggestions` ✅

- **app/models/player_journal.py**:
  - `PlayerJournalEntry` ✅

#### Request/Response Models:
- **app/models/requests.py**:
  - `NewGameRequest` ✅
  - `NewGameResponse` ✅
  - `ResumeGameResponse` ✅
  - `PlayerActionRequest` ✅
  - `CreateJournalEntryRequest` ✅
  - `UpdateJournalEntryRequest` ✅
  - Many more...

### DOES NOT EXIST:
- ❌ `app.models.quest` - NO Quest model exists
- ❌ `Initiative` class in combat.py
- ❌ `AIStreamChunk`, `AICompleteResponse`, `AIErrorResponse`
- ❌ `Character`, `Combat`, `Combatant`, `Location`, `NPC`, `Party`, `Spell`

## Correct Schema Export Structure

Based on user guidance and actual models, the correct structure should be:

```python
from app.models.ai_response import (
    NarrativeChunkResponse,
    CompleteResponse,
    ErrorResponse,
)
from app.models.character import CharacterSheet
from app.models.combat import CombatState, CombatParticipant
from app.models.damage_type import DamageType
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.models.memory import MemoryEntry
from app.models.npc import NPCSheet
from app.models.party import PartyState
from app.models.spell import SpellDefinition
from app.models.tool_suggestion import ToolSuggestion
```

## Impact Assessment

### Files That Will Break:
1. **Frontend Type Generation**: All generated TypeScript types will be wrong
2. **All TypeScript Files Using GameState**: Will have incorrect property access
3. **Test Files**: May have wrong type expectations
4. **API Integration**: Frontend won't match backend structure

### Required Fixes:
1. ✅ Fix `app/api/routers/schemas.py` imports and exports
2. ✅ Regenerate TypeScript types in frontend-v2
3. ✅ Fix ALL TypeScript files that use the generated types
4. ✅ Update test files to match new types
5. ✅ Verify all 133 tests still pass
6. ✅ Verify TypeScript compilation passes

## Next Steps

1. Fix schemas.py with correct imports
2. Regenerate types: `cd frontend-v2 && npm run generate:types`
3. Fix TypeScript errors file by file
4. Run tests and fix any failures
5. Commit all fixes with comprehensive documentation
