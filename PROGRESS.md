# Implementation Progress: ToolSuggestor Agent

This document tracks implementation progress against [PLAN.md](PLAN.md).

## Phase 0: Agent Configuration System (Data-Driven)

### ✅ 0.1: Create data/agents/ directory structure
- Created `data/agents/` directory for agent configurations

### ✅ 0.2: Create agent configuration Pydantic models
- Created `app/models/agent_config.py` with AgentConfig, AgentModelConfig, AgentRegistry
- Created `app/models/tool_suggestion_config.py` with RuleConfig, SuggestionConfig, PatternConfig

### ✅ 0.3: Create AgentConfigLoader service
- Created `app/services/ai/config_loader.py` with validation logic

### ✅ 0.4: Migrate system prompts to external files
**Design Change**: Instead of embedding prompts in JSON, we now:
- Store prompts in markdown files (`data/agents/prompts/*.md`)
- JSON references the markdown file via `system_prompt_file` field
- Loader reads and validates markdown files at startup
- **Rationale**: Better readability, easier diffs, cleaner separation of config vs content

**Status**: Complete
- [x] Updated models to use `system_prompt_file: str`
- [x] Updated loader to read markdown files (returns tuple of config + prompt)
- [x] Created markdown files for all 5 agent types
- [x] Updated JSON configs to reference markdown files
- [x] Loader validates markdown files exist and are non-empty at startup

### ✅ 0.5: Create tool_suggestion_rules.json
**Status**: Complete
- [x] Created comprehensive rule set with 10 heuristic rules
- [x] Rules cover: HP damage, combat initiation, quests, inventory, locations, time, dice rolls, party, conditions, spells
- [x] Each rule has patterns with weights, suggestions with confidence multipliers
- [x] Global settings include thresholds and rule priority order
- [x] Fully typed and validated against ToolSuggestionRulesConfig model

### ✅ 0.6: Update AgentFactory to stateful instance
**Status**: Complete
- [x] Converted AgentFactory from static class to stateful instance
- [x] Added `__init__` accepting AgentConfigLoader dependency
- [x] Load all 5 agent configs at initialization (fail-fast)
- [x] Added `_config_to_model_settings` helper
- [x] All agent creation now uses loaded configurations

### ✅ 0.7: Update Container to inject factory dependencies
**Status**: Complete
- [x] Created `agent_config_loader` cached property in Container
- [x] Created `agent_factory` cached property using loader
- [x] Updated all `AgentFactory.create_agent` calls to `self.agent_factory.create_agent`
- [x] Updated AgentLifecycleService to receive agent_factory as dependency
- [x] All agent creation now flows through configured factory instance

### ✅ 0.8: Add startup validation in main.py
**Status**: Complete
- [x] Added explicit agent configuration validation step in lifespan
- [x] Triggers `container.agent_factory` which loads and validates all configs
- [x] Fail-fast on startup if any configuration is invalid
- [x] Clear logging of validation success

### ✅ 0.9: Remove hardcoded prompts.py
**Status**: Complete
- [x] Updated CombatAgent to accept and use `system_prompt` parameter
- [x] Updated SummarizerAgent to accept and use `system_prompt` parameter (5 usage sites)
- [x] Updated IndividualMindAgent to accept and use `system_prompt` parameter
- [x] Updated PuppeteerAgent to accept and use `system_prompt` parameter
- [x] Updated NarrativeAgent to accept and use `system_prompt` parameter
- [x] Updated AgentFactory to pass loaded prompts to all agent constructors
- [x] Removed `app/agents/core/prompts.py` file
- [x] Verified no remaining imports of prompts module

## Phase 1: Tool Suggestion Infrastructure

### ✅ 1.1: Create tool suggestion models
**Status**: Complete
- [x] Created `app/models/tool_suggestion.py` with ToolSuggestion and ToolSuggestions models
- [x] Added `IToolSuggestionService` interface to `app/interfaces/services/ai.py`
- [x] Removed redundant `context_notes` field (deferred to ContextService)
- [x] Implemented `format_for_prompt()` method for markdown formatting
- [x] Full validation: confidence (0.0-1.0), non-empty tool_name and reason
- [x] Unit tests: 12 tests covering validation, formatting, truncation

### ✅ 1.2: Implement heuristic rule classes
**Status**: Complete
- [x] Created `app/services/ai/tool_suggestion/heuristic_rules.py`
- [x] Implemented abstract `HeuristicRule` base class with pattern matching
- [x] Implemented 6 concrete rule classes:
  - QuestProgressionRule
  - InventoryChangeRule
  - CurrencyTransactionRule
  - PartyManagementRule
  - TimePassageRule
  - LocationTransitionRule
- [x] Pattern compilation with case-insensitive regex matching
- [x] Confidence calculation: base × pattern_weight × confidence_multiplier (capped at 1.0)
- [x] Agent type filtering and required context checking
- [x] RULE_CLASSES registry for dynamic instantiation
- [x] Unit tests: 11 tests covering pattern matching, confidence, edge cases

### ✅ 1.3: Create ToolSuggestionService
**Status**: Complete
- [x] Created `app/services/ai/tool_suggestion/tool_suggestion_service.py`
- [x] Implements `IToolSuggestionService` interface
- [x] Rule evaluation pipeline:
  1. Evaluate all rules against prompt + game state
  2. Filter by minimum confidence threshold
  3. Deduplicate by tool_name (keep highest confidence)
  4. Sort by confidence descending
  5. Limit to max_suggestions
- [x] Error handling: logs rule exceptions, continues processing
- [x] Logging: detailed debug info on rule evaluation
- [x] Unit tests: 9 tests covering filtering, deduplication, sorting, limits, error handling
- [x] Package structure: `app/services/ai/tool_suggestion/__init__.py` exports

**Test Results**:
- ✅ 30 new tests (all passing)
- ✅ 293 total tests passing
- ✅ mypy --strict: no issues (292 source files)

## Phase 2: ToolSuggestor Agent

### ✅ 2.1: Implement ToolSuggestorAgent
**Status**: Complete
- [x] Created `app/agents/tool_suggestor/agent.py` with ToolSuggestorAgent class
- [x] Extends BaseAgent interface for consistency and future LLM integration
- [x] Accepts structured prompt format: `TARGET_AGENT: {agent_type}\n\nUSER_PROMPT: {prompt}`
- [x] Calls IToolSuggestionService for heuristic-based suggestions
- [x] Returns ToolSuggestions wrapped in StreamEvent (COMPLETE type)
- [x] Error handling: returns empty suggestions on parse/evaluation errors
- [x] Full logging for debugging and monitoring
- [x] Created `app/agents/tool_suggestor/__init__.py` for package structure

### ✅ 2.2: Integrate with AgentFactory
**Status**: Complete
- [x] Added `TOOL_SUGGESTOR = "tool_suggestor"` to AgentType enum in `app/agents/core/types.py`
- [x] Imported ToolSuggestorAgent in `app/agents/factory.py`
- [x] Added `IToolSuggestionService` to factory imports
- [x] Created `create_tool_suggestor_agent()` method in AgentFactory
- [x] Method accepts `suggestion_service` parameter and returns ToolSuggestorAgent instance
- [x] No configuration file needed (uses heuristic rules from tool_suggestion_rules.json)

## Phase 3: Orchestrator Integration

### ✅ 3.1: Update BaseAgent signature (BREAKING CHANGE)
**Status**: Complete
- [x] Updated `BaseAgent.process()` signature in `app/agents/core/base.py`
- [x] Added required `context: str` parameter between `game_state` and `stream`
- [x] New signature: `process(prompt: str, game_state: GameState, context: str, stream: bool = True)`
- [x] Updated docstring to document all parameters
- [x] **Breaking change**: All agents must now accept context parameter

### ✅ 3.2: Update all agent implementations
**Status**: Complete

#### NarrativeAgent (`app/agents/narrative/agent.py`)
- [x] Updated `process()` method signature to include `context: str` parameter
- [x] Removed internal `context_service.build_context()` call (now passed in)
- [x] Removed `context_service` from class attributes
- [x] Removed `IContextService` from imports
- [x] Updated AgentFactory to not pass `context_service` to constructor

#### CombatAgent (`app/agents/combat/agent.py`)
- [x] Updated `process()` method signature to include `context: str` parameter
- [x] Removed internal `context_service.build_context()` call (now passed in)
- [x] Removed `context_service` from class attributes
- [x] Removed `IContextService` from imports
- [x] Updated AgentFactory to not pass `context_service` to constructor

#### SummarizerAgent (`app/agents/summarizer/agent.py`)
- [x] Updated `process()` method signature to include `context: str` parameter
- [x] Added note: parameter unused but required by BaseAgent interface

#### BaseNPCAgent (`app/agents/npc/base.py`)
- [x] Updated `process()` method signature to include `context: str` parameter
- [x] Added docstring note: context unused for NPC agents (build their own internally)
- [x] NPCs build context internally with persona-specific information

#### ToolSuggestorAgent (`app/agents/tool_suggestor/agent.py`)
- [x] Already implemented with correct signature
- [x] Context parameter documented as unused (only needs game_state + prompt)

### ✅ 3.3: Update AgentOrchestrator
**Status**: Complete

#### Core Orchestrator Changes (`app/services/ai/orchestrator_service.py`)
- [x] Added `tool_suggestor_agent: ToolSuggestorAgent` parameter to `__init__()`
- [x] Added `context_service: IContextService` parameter to `__init__()`
- [x] Imported `ToolSuggestorAgent` and `IContextService`
- [x] Imported `ToolSuggestions` model
- [x] Updated `process()` method to:
  1. Build context using `context_service.build_context(game_state, agent_type)`
  2. Create structured prompt for ToolSuggestorAgent
  3. Call `tool_suggestor_agent.process()` to get suggestions
  4. Extract ToolSuggestions from StreamEvent
  5. Enrich context with formatted suggestions if any exist
  6. Pass enriched context to target agent's `process()` method
- [x] Updated NPC dialogue routing to pass empty context (NPCs build their own)
- [x] Updated combat aftermath narrative to build and pass context
- [x] Added imports for StreamEventType and ToolSuggestions

#### Combat Loop Changes (`app/services/ai/orchestrator/combat_loop.py`)
- [x] Added `context_service: IContextService` parameter to `run()` function
- [x] Added `context_service: IContextService` parameter to `_handle_auto_continue_turn()` helper
- [x] Added `context_service: IContextService` parameter to `_handle_combat_end()` helper
- [x] Imported `IContextService` and `AgentType`
- [x] All combat agent calls now build context via `context_service.build_context()`
- [x] NPC suggestion generation passes empty context (NPCs build their own)
- [x] Updated all callers in orchestrator_service.py to pass context_service

### ✅ 3.4: Update Container
**Status**: Complete
- [x] Created `tool_suggestor_agent` in `ai_service` property
- [x] Called `agent_factory.create_tool_suggestor_agent(suggestion_service=self.tool_suggestion_service)`
- [x] Passed `tool_suggestor_agent` to AgentOrchestrator constructor
- [x] Passed `context_service` to AgentOrchestrator constructor
- [x] All dependencies properly wired through DI

### ✅ 3.5: Update AI Response Models
**Status**: Complete
- [x] Updated `StreamEventContent` type alias in `app/models/ai_response.py`
- [x] Added `ToolSuggestions` to union: `str | NarrativeResponse | ToolSuggestions`
- [x] Imported ToolSuggestions from `app.models.tool_suggestion`
- [x] Updated docstring comment to include ToolSuggestions

### ✅ 3.6: Update All Tests
**Status**: Complete

#### Updated Test Files
- [x] `tests/integration/test_ai_response_flow.py`
  - Added `context: str` parameter to all stub agent `process()` methods
  - Added `IContextService` mock returning empty context
  - Added `ToolSuggestorAgent` stub returning empty suggestions
  - Updated AgentOrchestrator constructor calls

- [x] `tests/integration/test_orchestrator_multi_tool_flow.py`
  - Added `context: str` parameter to all stub agent `process()` methods
  - Created tool_suggestor_stub with method assignment
  - Updated AgentOrchestrator constructor call
  - Added type ignore comments for method assignment

- [x] `tests/unit/services/ai/test_agent_orchestrator.py`
  - Added `context: str` parameter to all stub agent `process()` methods
  - Added `IContextService` mock in `_build_orchestrator()`
  - Added `ToolSuggestorAgent` stub in `_build_orchestrator()`
  - Updated all AgentOrchestrator constructor calls
  - Added `yield` statements to satisfy async generator return type

- [x] `tests/unit/services/ai/test_agent_orchestrator_ally_combat.py`
  - Added `context: str` parameter to all stub agent `process()` methods
  - Added `IContextService` mock in `_build_orchestrator()`
  - Added `ToolSuggestorAgent` stub in `_build_orchestrator()`
  - Updated all AgentOrchestrator constructor calls
  - Added `yield` statements to satisfy async generator return type

- [x] `tests/unit/services/ai/test_combat_loop.py`
  - Updated all mock agent `process()` methods with `context: str` parameter

#### Test Results
- ✅ All 293 tests passing
- ✅ mypy --strict: no errors (all 293 source files)
- ✅ No regression in existing functionality

## Phase 4: Enhanced System Prompts

### ⏳ 4.1: Add tool suggestion sections to prompts
**Status**: Not started

## Phase 5: Party-Aware Context

### ⏳ 5.1: Update MessageConverterService
**Status**: Not started

### ⏳ 5.2: Update ContextService builders
**Status**: Not started

## Phase 6: Testing & Validation

### ⏳ 6.1: Write unit tests
**Status**: Not started

### ⏳ 6.2: Write integration tests
**Status**: Not started

### ⏳ 6.3: Full system validation
**Status**: Not started

## Design Changes & Improvements

### Markdown-based System Prompts
**Proposed by**: User feedback during implementation
**Status**: Complete
**Changes**:
- Models: `system_prompt: str` → `system_prompt_file: str`
- Loader: Added markdown file reading and validation
- Structure: `data/agents/prompts/*.md` for all prompts
- JSON configs reference markdown paths

**Benefits**:
- Better readability and maintainability
- Easier code review (diffs)
- Cleaner separation: JSON=config, MD=content
- Aligns with "content as data" principle

## ✅ Phase 0 Complete!

All Phase 0 tasks (0.1-0.9) are complete. The system now features:
- **Data-driven agent configuration** loaded from JSON + markdown files
- **Fail-fast validation** at application startup
- **Stateful AgentFactory** with proper dependency injection
- **Markdown-based system prompts** for better maintainability
- **Comprehensive tool suggestion rules** (10 heuristic rules ready for Phase 1)

## ✅ Phase 1 Complete!

All Phase 1 tasks (1.1-1.3) are complete. The system now features:
- **Tool suggestion models** with validation and markdown formatting
- **Heuristic rule system** with 6 implemented rule types and extensible base class
- **ToolSuggestionService** with complete pipeline: evaluation → filtering → deduplication → sorting → limiting
- **Full interface adherence** following SOLID principles with IToolSuggestionService
- **Comprehensive test coverage** with 30 new tests (all passing)
- **Type safety** verified with mypy --strict (no issues)

## ✅ Phase 2 Complete!

All Phase 2 tasks (2.1-2.2) are complete. The system now features:
- **ToolSuggestorAgent** implementing BaseAgent interface for consistency
- **Structured prompt format** for agent type targeting and user prompt separation
- **Factory integration** with `create_tool_suggestor_agent()` method
- **TOOL_SUGGESTOR** enum added to AgentType for routing
- **Error handling** with empty suggestions fallback
- **Full logging** for debugging and monitoring

## ✅ Phase 3 Complete!

All Phase 3 tasks (3.1-3.6) are complete. This was a **BREAKING CHANGE** phase. The system now features:
- **Updated BaseAgent interface** requiring `context: str` parameter in all `process()` methods
- **All agent implementations updated** (Narrative, Combat, Summarizer, NPC agents)
- **Context building centralized** in AgentOrchestrator before agent invocation
- **ToolSuggestorAgent integration** in orchestrator flow:
  1. Build context for target agent
  2. Generate tool suggestions via ToolSuggestorAgent
  3. Enrich context with suggestions
  4. Pass enriched context to target agent
- **Combat loop updated** to pass context_service and build context for all agent calls
- **Container wired** with tool_suggestor_agent and context_service dependencies
- **StreamEventContent extended** to support ToolSuggestions
- **All tests updated** and passing (293/293)
- **Type safety maintained** with mypy --strict (no errors)
- **CLAUDE.md updated** with new architecture documentation

## Next Steps
1. ✅ Phase 0 complete (agent configuration system)
2. ✅ Phase 1 complete (tool suggestion infrastructure)
3. ✅ Phase 2 complete (ToolSuggestor Agent)
4. ✅ Phase 3 complete (Orchestrator integration with BREAKING CHANGES)
5. ⏳ Phase 4: Enhanced system prompts
6. ⏳ Phase 5: Party-aware context
7. ⏳ Phase 6: Testing & validation
