# Data and Save Organization Refactoring Plan

## Overview
This document outlines the comprehensive plan to reorganize the data/ and saves/ directories to avoid large monolithic files and prepare for future features like a memory system. The refactoring follows SOLID principles and creates a more modular, maintainable architecture.

## Current Problems
1. **Monolithic Files**: `scenario.json` is 1093 lines, `characters.json` contains all characters
2. **Flat Structure**: No logical organization of related data
3. **Large Save Files**: Saves grow unbounded with all data in single files
4. **SOLID Violations**: Services have multiple responsibilities
5. **No Location State Tracking**: Environmental changes not persisted
6. **NPC Mentions Not Tracked**: `npcs_mentioned` field not populated

## New Directory Structure

### Data Directory Organization
```
data/
├── characters/
│   ├── aldric-swiftarrow.json          # Individual character file
│   ├── elena-moonwhisper.json          # Each character in own file
│   └── ...
│
├── scenarios/
│   └── [scenario-id]/                  # e.g., goblin-cave-adventure/
│       ├── scenario.json                # Metadata and references only
│       │   {
│       │     "id": "goblin-cave-adventure",
│       │     "title": "The Goblin Cave Adventure",
│       │     "description": "...",
│       │     "starting_location": "tavern",
│       │     "locations": ["tavern", "forest-path", ...],
│       │     "npcs": ["barkeep-tom", "goblin-warrior", ...],
│       │     "quests": ["find-the-artifact", ...],
│       │     "encounters": ["forest-ambush", ...],
│       │     "progression": "acts"
│       │   }
│       │
│       ├── locations/
│       │   ├── tavern.json
│       │   ├── forest-path.json
│       │   ├── goblin-cave-entrance.json
│       │   ├── goblin-cave-depths.json
│       │   └── treasure-room.json
│       │
│       ├── npcs/
│       │   ├── barkeep-tom.json
│       │   ├── merchant-elena.json
│       │   ├── goblin-warrior.json
│       │   ├── goblin-archer.json
│       │   └── goblin-boss.json
│       │
│       ├── quests/
│       │   ├── find-the-artifact.json
│       │   ├── rescue-the-merchant.json
│       │   └── defeat-the-goblin-boss.json
│       │
│       ├── encounters/
│       │   ├── forest-ambush.json
│       │   ├── cave-entrance-guards.json
│       │   └── boss-fight.json
│       │
│       └── progression/
│           └── acts.json
│
├── items.json      # Shared item definitions
├── spells.json     # Shared spell definitions
└── monsters.json   # Shared monster templates
```

### Save Directory Organization
```
saves/
└── [scenario-id]/                       # e.g., goblin-cave-adventure/
    └── [game-id]/                       # e.g., aldric-swiftarrow-20250831-0048-7fde3f61/
        ├── metadata.json
        │   {
        │     "game_id": "aldric-swiftarrow-20250831-0048-7fde3f61",
        │     "created_at": "2025-08-31T00:48:34.630695",
        │     "last_saved": "2025-08-31T01:23:45.123456",
        │     "character_source": "aldric-swiftarrow",
        │     "scenario_source": "goblin-cave-adventure",
        │     "current_location": "forest-path",
        │     "game_time": {...},
        │     "session_number": 1,
        │     "total_play_time_minutes": 35
        │   }
        │
        ├── character.json                # Current character state
        │
        ├── conversation_history.json     # All messages with metadata
        │
        ├── game_events.json              # Tool calls, dice rolls, state changes
        │
        ├── location_states/
        │   ├── tavern.json
        │   │   {
        │   │     "location_id": "tavern",
        │   │     "visited": true,
        │   │     "first_visited": "2025-08-31T00:48:34.630695",
        │   │     "last_visited": "2025-08-31T00:52:12.456789",
        │   │     "environmental_changes": {
        │   │       "bar_fight_happened": true,
        │   │       "secret_door_opened": false
        │   │     },
        │   │     "loot_taken": ["healing-potion", "rope"],
        │   │     "npcs_met": ["barkeep-tom"],
        │   │     "custom_flags": {}
        │   │   }
        │   └── forest-path.json
        │
        ├── npcs/
        │   ├── goblin-warrior-1.json    # Unique ID for duplicates
        │   ├── goblin-warrior-2.json
        │   ├── barkeep-tom.json
        │   └── merchant-elena.json
        │
        └── quests/
            ├── find-the-artifact.json
            │   {
            │     "quest_id": "find-the-artifact",
            │     "status": "active",
            │     "objectives_completed": ["speak_to_merchant"],
            │     "started_at": "2025-08-31T00:55:00.000000",
            │     "completed_at": null,
            │     "custom_flags": {}
            │   }
            └── rescue-the-merchant.json
```

## Implementation Phases

### Phase 1: Core Infrastructure (Foundation)
**Goal**: Create the foundational services and interfaces

1. **PathResolver Service**
   - Interface: `IPathResolver`
   - Implementation: `PathResolver`
   - Methods:
     - `get_data_dir() -> Path`
     - `get_saves_dir() -> Path`
     - `get_scenario_dir(scenario_id: str) -> Path`
     - `get_character_file(character_id: str) -> Path`
     - `get_save_dir(scenario_id: str, game_id: str) -> Path`
     - `resolve_scenario_component(scenario_id: str, component: str, item_id: str) -> Path`

2. **Base Repository Pattern**
   - Interface: `IRepository[T]`
   - Abstract class: `BaseRepository[T]`
   - Common functionality: caching, loading, error handling

3. **Base Loader Pattern**
   - Interface: `ILoader[T]`
   - Abstract class: `BaseLoader[T]`
   - Common functionality: file reading, validation

### Phase 2: Data Layer
**Goal**: Implement repositories for shared data

1. **Item Repository**
   - Loads from `data/items.json`
   - Caches all items in memory
   - Methods: `get_item()`, `list_items()`, `validate_item_reference()`

2. **Monster Repository**
   - Loads from `data/monsters.json`
   - Caches all monsters in memory
   - Methods: `get_monster()`, `list_monsters()`, `validate_monster_reference()`

3. **Spell Repository**
   - Loads from `data/spells.json`
   - Caches all spells in memory
   - Methods: `get_spell()`, `list_spells()`, `validate_spell_reference()`

4. **Character Loader**
   - Loads from `data/characters/[character-id].json`
   - Methods: `load_character()`, `list_characters()`, `validate_character()`

### Phase 3: Scenario System
**Goal**: Handle the new scenario structure

1. **Scenario Loader**
   - Loads scenario metadata from `scenario.json`
   - Lazy-loads components as needed
   - Methods: `load_scenario()`, `load_component()`, `list_scenarios()`

2. **Location Service**
   - Manages location data and state
   - Methods: `get_location()`, `update_location_state()`, `get_connections()`

3. **NPC Service**
   - Manages NPC definitions and instances
   - Methods: `get_npc_definition()`, `create_npc_instance()`, `update_npc_state()`

4. **Quest Service**
   - Manages quest definitions and progress
   - Methods: `get_quest()`, `update_quest_progress()`, `check_objectives()`

5. **Encounter Service**
   - Manages encounter definitions
   - Methods: `get_encounter()`, `spawn_monsters()`, `check_triggers()`

### Phase 4: Save System
**Goal**: Implement modular save/load system

1. **Save Manager**
   - Orchestrates save/load operations
   - Methods: `save_game()`, `load_game()`, `list_saves()`
   - Delegates to component-specific savers

2. **Component Savers**
   - `save_metadata()`, `load_metadata()`
   - `save_character()`, `load_character()`
   - `save_conversation_history()`, `load_conversation_history()`
   - `save_game_events()`, `load_game_events()`
   - `save_location_states()`, `load_location_states()`
   - `save_npcs()`, `load_npcs()`
   - `save_quests()`, `load_quests()`

3. **Location State Tracking**
   - New model: `LocationState`
   - Tracks: visited timestamps, environmental changes, loot taken
   - Persisted in `location_states/` directory

### Phase 5: Game Management
**Goal**: Refactor existing GameService following SOLID

1. **Game State Manager**
   - Manages active game state in memory
   - Methods: `get_game()`, `update_game()`, `create_game()`

2. **Message Manager**
   - Handles conversation history
   - Methods: `add_message()`, `get_history()`, `extract_metadata()`

3. **Event Manager**
   - Handles game events
   - Methods: `add_event()`, `get_events()`, `process_event()`

4. **Metadata Service**
   - Extracts metadata from messages
   - Methods: `extract_npc_mentions()`, `get_current_location()`, `get_combat_round()`

### Phase 6: Integration
**Goal**: Wire everything together

1. **Update Container**
   - Register all new services
   - Update dependency injection

2. **Update Agents and Tools**
   - Update all references to use new services
   - Test all execution paths

3. **Data Migration**
   - Create migration script for existing data
   - Reorganize files into new structure
   - No save migration (abandon old saves)

## Key Design Decisions

### 1. Separation of Concerns (SOLID - Single Responsibility)
- Each service has one clear responsibility
- Repositories handle data access
- Loaders handle file operations
- Managers handle business logic
- Services handle domain-specific operations

### 2. Dependency Inversion
- All services depend on interfaces, not implementations
- Easy to swap implementations
- Testable architecture

### 3. Open/Closed Principle
- New scenario components can be added without modifying existing code
- New save components can be added without changing SaveManager

### 4. Interface Segregation
- Small, focused interfaces
- Clients only depend on methods they use
- No "fat" interfaces

### 5. Liskov Substitution
- All implementations can be substituted for their interfaces
- Consistent behavior across implementations

## Benefits

### Immediate Benefits
1. **No More Huge Files**: Scenarios split into manageable pieces
2. **Better Organization**: Clear structure for data and saves
3. **Faster Loading**: Only load what's needed
4. **Easier Debugging**: Isolated components
5. **NPC Tracking**: Properly populated `npcs_mentioned` field

### Future Benefits
1. **Memory System Ready**: Conversation history can be chunked
2. **Parallel Development**: Multiple developers can work on different components
3. **Easy Extensions**: Add new components without touching existing code
4. **Performance**: Can optimize individual components
5. **Testing**: Each component can be tested in isolation

## Migration Strategy

### Data Migration Script
```python
# Pseudocode for migration
def migrate_data():
    # 1. Create new directory structure
    create_directories()
    
    # 2. Split characters.json
    for character in load_old_characters():
        save_character_file(character)
    
    # 3. Split scenario.json
    scenario = load_old_scenario()
    save_scenario_metadata(scenario)
    save_locations(scenario.locations)
    save_npcs(scenario.npcs)
    save_quests(scenario.quests)
    save_encounters(scenario.encounters)
    save_progression(scenario.progression)
    
    # 4. Copy shared data files
    copy_items_spells_monsters()
```

### No Save Migration
- Old saves will not be migrated
- Users will need to start new games
- Clean break from old structure

## Success Criteria

1. **All tests pass** with new structure
2. **No performance degradation**
3. **Can create new game** with reorganized data
4. **Can save/load games** with new structure
5. **Location states** properly tracked
6. **NPC mentions** properly extracted
7. **All SOLID principles** followed
8. **Code is more maintainable** than before

## Risk Mitigation

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Implement incrementally, test each phase

2. **Risk**: Performance issues with many small files
   - **Mitigation**: Implement caching, lazy loading

3. **Risk**: Complex dependency management
   - **Mitigation**: Clear interfaces, proper DI container

4. **Risk**: Data inconsistency
   - **Mitigation**: Validation at load time, fail fast

## Timeline Estimate

- Phase 1: 2-3 hours (Core Infrastructure) ✅ COMPLETED
- Phase 2: 2-3 hours (Data Layer) ✅ COMPLETED
- Phase 3: 3-4 hours (Scenario System) ✅ COMPLETED
- Phase 4: 3-4 hours (Save System) ✅ COMPLETED
- Phase 5: 2-3 hours (Game Management) ✅ COMPLETED
- Phase 5.5: 1-2 hours (Service Reorganization) ✅ COMPLETED
- Phase 6: 2-3 hours (Integration) ✅ COMPLETED

**Total: 14-20 hours of implementation**

## Implementation Progress

### Completed (2025-08-31)

#### Phase 1: Core Infrastructure ✅
- Created `PathResolver` service for consistent file path resolution
- Implemented `BaseRepository` abstract class with caching and common data access patterns
- Implemented `BaseLoader` abstract class for file operations
- Added interfaces to `IPathResolver`, `IRepository<T>`, and `ILoader<T>`

#### Phase 2: Data Layer ✅
- Implemented `ItemRepository` for managing item definitions
- Implemented `MonsterRepository` for managing monster/NPC data
- Implemented `SpellRepository` for managing spell definitions with case-insensitive lookup
- Implemented `CharacterLoader` for loading character sheets from individual files
- All repositories support caching, lazy loading, and filtering operations

#### Phase 3: Scenario System ✅
- Created `ScenarioLoader` for loading modular scenario structure
- Implemented loading of locations from scenarios/[id]/locations/
- Implemented loading of quests from scenarios/[id]/quests/
- Implemented loading of progression/acts from scenarios/[id]/progression/
- Updated `ScenarioService` to use `ScenarioLoader` via dependency injection
- Updated `GameService` to receive `ScenarioService` via dependency injection
- Updated container to properly inject all dependencies
- Created sample scenario files for goblin-cave-adventure with modular structure
- Verified scenario loading works with all components

#### Phase 4: Save System ✅
- Created `ISaveManager` interface for managing game save operations
- Implemented `SaveManager` class with modular save/load functionality
- Updated `GameService` to use `SaveManager` instead of direct file operations
- Wired `SaveManager` in the container with proper dependency injection
- Tested save/load functionality with modular file structure
- Save structure now properly organized as:
  - saves/[scenario-id]/[game-id]/
    - metadata.json (game metadata)
    - character.json (character state)
    - conversation_history.json (chat messages)
    - game_events.json (tool calls and events)
    - location_states/ (location tracking)
    - npcs/ (active NPCs)
    - quests/ (active quests)

#### Phase 5: Game Management ✅
- Created `IGameStateManager` interface for managing active game states in memory
- Created `IMessageManager` interface for managing conversation history
- Created `IEventManager` interface for managing game events
- Created `IMetadataService` interface for extracting metadata from messages
- Implemented `GameStateManager` to handle in-memory game storage
- Implemented `MessageManager` to handle conversation history operations
- Implemented `EventManager` to handle game event operations
- Implemented `MetadataService` to extract NPCs mentioned, location, and combat round from messages
- Refactored `GameService` to delegate responsibilities to the new managers
- Updated container to wire all new services together
- Tested all new services and verified proper operation

### Phase 5.5: Service Reorganization (Domain-Driven Structure)

**Goal**: Reorganize services into domain-specific modules for better maintainability and future extensibility.

#### Improved Service Structure

```
app/
├── services/
│   ├── common/                    # Shared infrastructure services
│   │   ├── __init__.py
│   │   ├── path_resolver.py       # PathResolver - file path resolution
│   │   ├── broadcast_service.py   # BroadcastService - SSE event streaming
│   │   └── dice_service.py        # DiceService - dice rolling mechanics
│   │
│   ├── data/                      # Data access layer (ALL persistence)
│   │   ├── __init__.py
│   │   ├── repositories/          # In-memory data repositories
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── item_repository.py
│   │   │   ├── monster_repository.py
│   │   │   └── spell_repository.py
│   │   └── loaders/              # File loading/saving operations
│   │       ├── __init__.py
│   │       ├── base_loader.py
│   │       ├── character_loader.py  # Loads character JSON files
│   │       └── scenario_loader.py   # Loads scenario JSON files
│   │
│   ├── character/                 # Character domain services
│   │   ├── __init__.py
│   │   ├── character_service.py   # Character business logic
│   │   └── future/                # Placeholder for future services
│   │       ├── class_service.py   # Class features and progression
│   │       ├── level_service.py   # Level up mechanics
│   │       ├── race_service.py    # Race/subrace features
│   │       └── feat_service.py    # Feats and abilities
│   │
│   ├── scenario/                  # Scenario domain services
│   │   ├── __init__.py
│   │   ├── scenario_service.py    # Scenario business logic
│   │   ├── location_service.py    # Location management
│   │   ├── npc_service.py         # NPC management
│   │   ├── quest_service.py       # Quest tracking
│   │   └── encounter_service.py   # Encounter management
│   │
│   ├── game/                      # Game state management
│   │   ├── __init__.py
│   │   ├── game_service.py        # Main game orchestrator
│   │   ├── game_state_manager.py  # In-memory state management
│   │   ├── save_manager.py        # Save/load operations
│   │   ├── message_manager.py     # Conversation history
│   │   ├── event_manager.py       # Game events
│   │   └── metadata_service.py    # Metadata extraction
│   │
│   ├── ai/                        # AI and agent services
│   │   ├── __init__.py
│   │   ├── ai_service.py          # Main AI service
│   │   ├── context_service.py     # Context building
│   │   ├── message_service.py     # Message handling/broadcasting
│   │   ├── message_converter.py   # Message format conversion
│   │   └── event_logger.py        # Event logging for AI
│   │
│   └── __init__.py
```

#### Implementation Steps

1. **Create domain directories**
   - `app/services/character/`
   - `app/services/scenario/`
   - `app/services/ai/`
   - Update `app/services/common/`

2. **Move character services**
   - Move `character_service.py` → `character/character_service.py`
   - Keep `data/loaders/character_loader.py` in data layer
   - Create placeholder files for future services

3. **Move scenario services**
   - Move `scenario_service.py` → `scenario/scenario_service.py`
   - Keep `data/loaders/scenario_loader.py` in data layer
   - Create location, npc, quest, encounter services (extract from current code if applicable)

4. **Move game services**
   - Move `game_service.py` → `game/game_service.py`
   - Keep existing game/ subdirectory services

5. **Move AI services**
   - Move `ai_service.py` → `ai/ai_service.py`
   - Move `context_service.py` → `ai/context_service.py`
   - Move `message_service.py` → `ai/message_service.py`
   - Move helper services to ai/ directory

6. **Move common services**
   - Move `dice_service.py` → `common/dice_service.py`
   - Move `broadcast_service.py` → `common/broadcast_service.py`
   - Keep `path_resolver.py` in common/

7. **Update all imports**
   - Update container imports
   - Update cross-service imports
   - Update agent imports
   - Update route imports

8. **Verify functionality**
   - Test service initialization
   - Test game creation and operations
   - Test AI agent functionality

#### Benefits of New Structure

1. **Domain Separation**: Each domain (character, scenario, game, AI) has its own module
2. **Future-Ready**: Character domain prepared for future features (classes, races, feats)
3. **Clear Responsibilities**: Each service module has a clear domain boundary
4. **Easier Navigation**: Related services are grouped together
5. **Scalability**: New services can be added to appropriate domains
6. **Reduced Coupling**: Services communicate through interfaces, not direct imports

#### Phase 5.5: Service Reorganization ✅
- Created domain-specific directory structure:
  - `app/services/character/` - Character domain services
  - `app/services/scenario/` - Scenario domain services
  - `app/services/ai/` - AI and agent services
  - `app/services/game/` - Game state management services
  - `app/services/common/` - Shared infrastructure services
- Moved services to appropriate domains:
  - Character services to `character/`
  - Scenario services to `scenario/`
  - AI services to `ai/`
  - Game services to `game/`
  - Common services to `common/`
- Kept data loaders in `data/loaders/` (proper separation of data access layer)
- Updated all imports throughout the codebase
- Updated container with new service paths
- Tested all services and workflows successfully

### Phase 6: Integration ✅
- Updated container with all new services properly wired
- Verified game creation with modular save structure
- Verified game loading from modular saves
- Verified AI agent integration with new services
- Verified tool execution through the event bus
- Tested complete workflow through API endpoints
- Confirmed all services work together seamlessly

### Implementation Completed
All phases of the refactoring plan have been successfully completed. The system now has:
- Fully modular data and save structure
- Clean separation of concerns following SOLID principles
- All services properly integrated and tested
- Working AI agent with tool execution
- Successful game creation, saving, and loading with the new architecture

## Conclusion

This refactoring will transform the codebase from a monolithic structure to a modular, maintainable architecture following SOLID principles. The new organization will support future features while solving current problems with large files and poor separation of concerns.