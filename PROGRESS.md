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

### ⏳ 1.1: Create tool suggestion models
**Status**: Not started

### ⏳ 1.2: Implement heuristic rule classes
**Status**: Not started

### ⏳ 1.3: Create ToolSuggestionService
**Status**: Not started

## Phase 2: ToolSuggestor Agent

### ⏳ 2.1: Implement ToolSuggestorAgent
**Status**: Not started

### ⏳ 2.2: Integrate with AgentFactory
**Status**: Not started

## Phase 3: Orchestrator Integration

### ⏳ 3.1: Update BaseAgent signature
**Status**: Not started

### ⏳ 3.2: Update all agent implementations
**Status**: Not started

### ⏳ 3.3: Update AgentOrchestrator
**Status**: Not started

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

## Next Steps
1. ✅ Phase 0 complete (agent configuration system)
2. ⏳ Phase 1: Tool Suggestion Infrastructure
3. ⏳ Phase 2-6: ToolSuggestorAgent, integration, enhanced prompts, party-aware context, testing
