# Implementation Plan: Tool Usage Verification System

## Executive Summary

Implement a general tool verification system to improve consistency in tool calling across all agents (Narrative, Combat, NPC). The system uses a **pre-flight advisory ToolSuggestorAgent** that analyzes context and suggests appropriate tools before agent execution, combined with **data-driven agent configuration**, **enhanced system prompts**, and **party-aware context sharing**.

**Primary Issues Addressed:**
- Missing tool calls (most common)
- Wrong tool arguments (occasional)
- Inconsistent tool usage across all agents
- NPC agents lack narrative context when appropriate
- System prompts hardcoded in Python files (not content-driven)

**Solution Components:**
1. **Agent Configuration System** - Data-driven prompts and tool suggestion rules
2. **ToolSuggestorAgent** - Pre-flight heuristic-based agent suggesting tools
3. **Enhanced System Prompts** - Concrete examples of tool usage patterns (in config)
4. **Party-Aware Context Sharing** - NPCs in party see narrative messages

---

## Architecture Overview

### Current Flow
```
User Input → Orchestrator → Agent → Response
```

### New Flow
```
User Prompt
    ↓
[Orchestrator] → determines agent type
    ↓
[Orchestrator] → builds base context via ContextService
    ↓
[Orchestrator] → calls ToolSuggestorAgent.process() for suggestions
    ↓
[Orchestrator] → enriches context with suggestions
    ↓
[Agent.process(prompt, game_state, enriched_context)] → processes with tools + suggestions
    ↓
Response
```

**Key Principles:**
- Orchestrator **owns context building** and enrichment (single responsibility)
- All agents receive context as required parameter (no optional params)
- ToolSuggestorAgent uses BaseAgent interface for consistency and future LLM integration

### Design Principles Alignment

✅ **SOLID:** Single responsibility (suggestor only suggests), Open/Closed (extensible rules), DI via container
✅ **Fail Fast:** Config validation at startup, type-safe models
✅ **Tool-Driven:** Agents orchestrate, business logic in services
✅ **Content as Data:** Prompts and rules in JSON, not Python code

---

## Phase 0: Agent Configuration System (Days 1-3)

**Goal:** Move system prompts and tool suggestion rules from Python to JSON for data-driven configuration.

### 0.1 Create Directory Structure

Create `data/agents/` with these files:
- `narrative.json` - Narrative agent config
- `combat.json` - Combat agent config
- `summarizer.json` - Summarizer agent config
- `npc_individual.json` - Individual NPC agent config
- `npc_puppeteer.json` - Puppeteer NPC agent config
- `tool_suggestion_rules.json` - Heuristic rules for tool suggestions

### 0.2 Create Configuration Models

**File:** `app/models/agent_config.py`

Create Pydantic models:
- `AgentModelConfig`: temperature, max_tokens, reasoning_effort, parallel_tool_calls
- `AgentConfig`: agent_type, system_prompt, model_config, description
- `AgentRegistry`: agents dict

**File:** `app/models/tool_suggestion_config.py`

Create Pydantic models:
- `PatternConfig`: pattern (regex), weight, description
- `SuggestionConfig`: tool_name, reason, confidence_multiplier, suggested_args
- `RuleConfig`: rule_id, rule_class, enabled, description, patterns, suggestions, applicable_agents, required_context, state_check, base_confidence
- `ToolSuggestionRulesConfig`: rules list, global_settings dict

### 0.3 Create Configuration Loader

**File:** `app/services/ai/config_loader.py`

Create `AgentConfigLoader` class with methods:
- `__init__(config_dir: Path)`: Store config directory path
- `load_agent_config(filename: str) -> AgentConfig`: Load and validate JSON → Pydantic model
- `load_tool_suggestion_rules() -> ToolSuggestionRulesConfig`: Load rules config

Use `json.load()` + `Pydantic.model_validate()` for type-safe loading.

### 0.4 Migrate System Prompts to JSON

For each agent JSON file, structure as:
```json
{
  "agent_type": "narrative",
  "description": "Expert Dungeon Master",
  "model_config": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "reasoning_effort": "high",
    "parallel_tool_calls": false
  },
  "system_prompt": "Full prompt text here..."
}
```

Copy existing prompts from `app/agents/core/prompts.py` into JSON files.

### 0.5 Create Tool Suggestion Rules Config

**File:** `data/agents/tool_suggestion_rules.json`

Structure:
```json
{
  "rules": [
    {
      "rule_id": "quest_acceptance",
      "rule_class": "QuestAcceptanceRule",
      "enabled": true,
      "description": "Suggest start_quest when user accepts a quest",
      "patterns": [
        {"pattern": "\\b(accept|take|start)\\b.*\\bquest\\b", "weight": 0.8}
      ],
      "suggestions": [
        {"tool_name": "start_quest", "reason": "User appears to be accepting a quest"}
      ],
      "applicable_agents": ["narrative", "npc"]
    }
  ],
  "global_settings": {
    "min_confidence_threshold": 0.5,
    "max_suggestions_per_request": 5
  }
}
```

Create rules for: quest acceptance, item transfer, combat end, next turn, damage application, location change, rests.

### 0.6 Update AgentFactory

**File:** `app/agents/factory.py`

**⚠️ PARADIGM SHIFT:** This changes the factory from **stateless classmethods** to **stateful instance with injected dependencies**. All factory methods become regular instance methods with access to pre-loaded configs and services.

Changes:
1. **Remove @classmethod decorators** from all factory methods (including `_create_model` and `_register_agent_tools`)
2. **Add `__init__` method**:
   ```python
   def __init__(
       self,
       config_loader: AgentConfigLoader,
       event_bus: IEventBus,
       scenario_service: IScenarioService,
       repository_provider: IRepositoryProvider,
       # ... all 10+ services that agents need
   ):
       self.config_loader = config_loader
       self.event_bus = event_bus
       # ... store all services

       # Load all configs at init (fail-fast)
       self.narrative_config = config_loader.load_agent_config("narrative.json")
       self.combat_config = config_loader.load_agent_config("combat.json")
       self.summarizer_config = config_loader.load_agent_config("summarizer.json")
       self.npc_individual_config = config_loader.load_agent_config("npc_individual.json")
       self.npc_puppeteer_config = config_loader.load_agent_config("npc_puppeteer.json")
   ```
3. **Change `create_agent(agent_type)` signature**:
   - Remove all service parameters
   - Keep only `agent_type: AgentType` parameter
   - Use stored services from `self`
4. **Use loaded configs**:
   - Replace `NARRATIVE_SYSTEM_PROMPT` with `self.narrative_config.system_prompt`
   - Replace hardcoded `OpenAIModelSettings(temperature=0.7, ...)` with `self.narrative_config.model_config`
5. **Same changes for `create_individual_mind_agent()` and `create_puppeteer_agent()`**

### 0.7 Update Container

**File:** `app/container.py`

Add config loader:
```python
@cached_property
def agent_config_loader(self) -> AgentConfigLoader:
    agents_dir = self.path_resolver.data_dir / "agents"
    return AgentConfigLoader(config_dir=agents_dir)
```

Add agent factory property:
```python
@cached_property
def agent_factory(self) -> AgentFactory:
    return AgentFactory(
        config_loader=self.agent_config_loader,
        event_bus=self.event_bus,
        scenario_service=self.scenario_service,
        repository_provider=self.repository_factory,
        metadata_service=self.metadata_service,
        event_manager=self.event_manager,
        save_manager=self.save_manager,
        conversation_service=self.conversation_service,
        context_service=self.context_service,
        event_logger_service=self.event_logger_service,
        action_service=self.action_service,
        tool_call_extractor_service=self.tool_call_extractor_service,
        message_service=self.message_service,
    )
```

Update `ai_service` property:
```python
@cached_property
def ai_service(self) -> IAIService:
    settings = get_settings()

    # Use factory instance methods instead of classmethods
    narrative_agent = self.agent_factory.create_agent(AgentType.NARRATIVE)
    combat_agent = self.agent_factory.create_agent(AgentType.COMBAT)

    # ... rest of orchestrator setup
```

Update `summarizer_agent` property similarly to use factory.

### 0.8 Add Startup Validation

**File:** `app/main.py` in `lifespan()` function

Add validation:
```python
# Validate agent configurations at startup
container.agent_config_loader.load_agent_config("narrative.json")
container.agent_config_loader.load_agent_config("combat.json")
# ... all 5 agent configs
container.agent_config_loader.load_tool_suggestion_rules()
logger.info("✓ Agent configurations validated")
```

### 0.9 Remove Hardcoded Prompts

**File:** `app/agents/core/prompts.py`

After Phase 0 complete:
1. Remove all imports of prompt constants
2. Update tests to use config-driven prompts
3. DELETE this file entirely

**Verification checklist:**
- [ ] No imports of `NARRATIVE_SYSTEM_PROMPT`, etc. remain (verify with: `grep -r "from app.agents.core.prompts import" app/`)
- [ ] All agents use `agent_config.system_prompt`
- [ ] All tests pass
- [ ] File deleted

---

## Phase 1: Core Tool Suggestion Infrastructure (Days 4-6)

**Goal:** Create heuristic-based tool suggestion system with config-driven rules. May become LLM-based in the future

### 1.1 Create Agent Type

**File:** `app/agents/core/types.py`

Add to AgentType enum:
```python
TOOL_SUGGESTOR = "tool_suggestor"
```

No separate interface needed - ToolSuggestorAgent will implement BaseAgent for consistency and future LLM integration.

### 1.2 Create Tool Suggestion Models

**File:** `app/models/tool_suggestion.py` (NEW)

Create Pydantic models:
- `ToolSuggestion`: tool_name, reason, confidence (0.0-1.0), arguments (optional)
- `ToolSuggestions`: suggestions list, context_notes list

Add method `format_for_prompt() -> str` that formats suggestions as markdown for agent context.

### 1.3 Create Heuristic Rules System

**File:** `app/services/ai/tool_suggestion/heuristic_rules.py` (NEW)

**Base Class:**
- `HeuristicRule(ABC)`: Takes `RuleConfig` in `__init__`
- Compiles regex patterns from config
- Abstract `evaluate()` method returns `list[ToolSuggestion]`
- Helper `_check_patterns(text)` checks all patterns, returns (matched, best_weight)
- Helper `_build_suggestions(confidence)` builds suggestions from config

**Concrete Rules:**
Create classes inheriting `HeuristicRule`:
- `QuestAcceptanceRule`: Checks if user accepting quest
- `ItemTransferRule`: Checks if items being given/taken
- `CombatEndRule`: Checks if all enemies defeated (state-based)
- `NextTurnRule`: Suggests next_turn in combat
- `DamageApplicationRule`: Suggests update_hp after damage
- `LocationChangeRule`: Suggests change_location for travel
- `RestRule`: Suggests rest tools

**Rule Registry:**
```python
RULE_CLASSES: dict[str, type[HeuristicRule]] = {
    "QuestAcceptanceRule": QuestAcceptanceRule,
    # ... all rule classes
}
```

### 1.4 Create Tool Suggestion Service

**File:** `app/services/ai/tool_suggestion/tool_suggestion_service.py` (NEW)

Create `ToolSuggestionService` class:
- `__init__(rules, min_confidence_threshold, max_suggestions)`: Store config
- `async suggest_tools(game_state, prompt, agent_type) -> ToolSuggestions`:
  - Evaluate all rules
  - Filter by confidence threshold
  - Deduplicate by tool_name (keep highest confidence)
  - Sort by confidence descending
  - Limit to max_suggestions
  - Add context notes based on game state
  - Return ToolSuggestions

Handle rule evaluation errors gracefully (log but don't fail).

---

## Phase 2: Agent Implementation (Days 7-8)

**Goal:** Create ToolSuggestorAgent and integrate with factory/container.

### 2.1 Create ToolSuggestorAgent

**File:** `app/agents/tool_suggestor/agent.py` (NEW)

Create `ToolSuggestorAgent(BaseAgent)` class:
- `__init__(suggestion_service)`: Store service
- `get_required_tools() -> list[ToolFunction]`: Return empty list (no tools needed)
- `async process(prompt, game_state, context, stream) -> AsyncIterator[StreamEvent]`:
  - Parse prompt format: `"TARGET_AGENT: {agent_type}\n\nUSER_PROMPT: {actual_prompt}"`
  - Extract target_agent_type and user_prompt from structured prompt
  - Call `suggestion_service.suggest_tools(game_state, user_prompt, target_agent_type)`
  - Yield `StreamEvent(type=StreamEventType.COMPLETE, content=suggestions)`
  - Log suggestions made

**Important:** The `context` parameter is **required by BaseAgent interface** but **unused** by this agent. This maintains consistency with all other agents and enables future LLM-based implementation without signature changes.

Uses BaseAgent interface for consistency and future LLM integration. Currently uses heuristics only.

### 2.2 Update Agent Factory

**File:** `app/agents/factory.py`

In `__init__`, add:
```python
def __init__(
    self,
    config_loader: AgentConfigLoader,
    tool_suggestion_service: ToolSuggestionService,  # NEW
    # ... other services
):
    # ... existing init code
    self.tool_suggestion_service = tool_suggestion_service
```

Update `create_agent()` method to handle TOOL_SUGGESTOR type:
```python
def create_agent(self, agent_type: AgentType) -> BaseAgent:
    # ... existing NARRATIVE, COMBAT, SUMMARIZER cases ...

    if agent_type == AgentType.TOOL_SUGGESTOR:
        return ToolSuggestorAgent(suggestion_service=self.tool_suggestion_service)

    raise ValueError(f"Unknown agent type: {agent_type}")
```

### 2.3 Update Container

**File:** `app/container.py`

Add tool suggestion service:
```python
@cached_property
def tool_suggestion_service(self) -> ToolSuggestionService:
    config = self.agent_config_loader.load_tool_suggestion_rules()

    # Instantiate rule classes from config
    rules = []
    for rule_config in config.rules:
        if not rule_config.enabled:
            continue
        rule_class = RULE_CLASSES[rule_config.rule_class]
        rules.append(rule_class(config=rule_config))

    return ToolSuggestionService(
        rules=rules,
        min_confidence_threshold=config.global_settings["min_confidence_threshold"],
        max_suggestions=config.global_settings["max_suggestions_per_request"],
    )
```

Update `agent_factory` property to inject service:
```python
@cached_property
def agent_factory(self) -> AgentFactory:
    return AgentFactory(
        config_loader=self.agent_config_loader,
        tool_suggestion_service=self.tool_suggestion_service,  # NEW
        event_bus=self.event_bus,
        # ... all other services
    )
```

---

## Phase 3: Integration with Orchestrator (Day 9)

**Goal:** Orchestrator explicitly enriches context with tool suggestions before calling agents.

### 3.1 Update BaseAgent Interface

**File:** `app/agents/core/base.py`

Update `process()` signature to require context:
```python
async def process(
    self,
    prompt: str,
    game_state: GameState,
    context: str,  # NEW: Required parameter, no default
    stream: bool = True,
) -> AsyncIterator[StreamEvent]:
```

**Rationale:** Context building moves to orchestrator for single responsibility. No backward compatibility - full migration.

**⚠️ BREAKING CHANGE:** This affects ALL agents in the system.

Update all agent implementations:
- **NarrativeAgent** ([app/agents/narrative/agent.py](app/agents/narrative/agent.py:124))
- **CombatAgent** ([app/agents/combat/agent.py])
- **SummarizerAgent** ([app/agents/summarizer/agent.py])
- **BaseNPCAgent** ([app/agents/npc/base.py](app/agents/npc/base.py:114)) (affects both IndividualMindAgent and PuppeteerAgent)

**Remove from agents:**
- `context_service: IContextService` dependency in `__init__`
- Calls to `context_service.build_context()`

**Update in agents:**
```python
async def process(
    self,
    prompt: str,
    game_state: GameState,
    context: str,  # Use provided context directly
    stream: bool = True,
) -> AsyncIterator[StreamEvent]:
    # OLD: context = self.context_service.build_context(game_state, agent_type)
    # NEW: Use provided context parameter directly

    message_history = self.message_converter.to_pydantic_messages(...)
    full_prompt = f"\n\n{context}\n\nPlayer: {prompt}"
    # ... rest of processing
```

### 3.2 Update Orchestrator Service

**File:** `app/services/ai/orchestrator_service.py`

Add to `AgentOrchestrator.__init__`:
```python
tool_suggestor_agent: ToolSuggestorAgent  # NEW parameter
context_service: IContextService  # Moved from agents to orchestrator
```

**Note:** `agent_router.select()` at line 100 doesn't need updates for TOOL_SUGGESTOR since it's never used in routing logic - the orchestrator calls it explicitly only when needed.

Add method to get suggestions:
```python
async def _get_tool_suggestions(
    self,
    game_state: GameState,
    prompt: str,
    agent_type: AgentType,
) -> ToolSuggestions:
    """Call ToolSuggestorAgent to get suggestions for target agent."""
    # Build structured prompt for suggestor agent
    suggestor_prompt = f"TARGET_AGENT: {agent_type.value}\n\nUSER_PROMPT: {prompt}"

    # Call suggestor agent via process() interface
    async for event in self.tool_suggestor_agent.process(
        prompt=suggestor_prompt,
        game_state=game_state,
        context="",  # Suggestor doesn't need context
        stream=False,
    ):
        if event.type == StreamEventType.COMPLETE:
            return event.content  # Returns ToolSuggestions object

    # Fallback if no suggestions
    return ToolSuggestions(suggestions=[], context_notes=[])
```

Update `process()` method:
```python
async def process(
    self,
    prompt: str,
    game_state: GameState,
    stream: bool = True,
) -> AsyncIterator[StreamEvent]:
    # 1. Determine agent type (existing code)
    current_agent_type = agent_router.select(game_state)

    # 2. Build base context (orchestrator now owns this)
    base_context = self.context_service.build_context(game_state, current_agent_type)

    # 3. Get tool suggestions for target agent
    suggestions = await self._get_tool_suggestions(game_state, prompt, current_agent_type)

    # 4. Enrich context with suggestions
    if suggestions.suggestions or suggestions.context_notes:
        enriched_context = f"{base_context}\n\n{suggestions.format_for_prompt()}"
    else:
        enriched_context = base_context

    # 5. Select and call agent with enriched context
    agent = self.combat_agent if current_agent_type == AgentType.COMBAT else self.narrative_agent
    async for event in agent.process(prompt, game_state, enriched_context, stream=stream):
        yield event
```

### 3.3 Update Container

**File:** `app/container.py`

Update `ai_service` property to inject dependencies:
```python
@cached_property
def ai_service(self) -> IAIService:
    narrative_agent = self.agent_factory.create_agent(AgentType.NARRATIVE)
    combat_agent = self.agent_factory.create_agent(AgentType.COMBAT)
    tool_suggestor_agent = self.agent_factory.create_agent(AgentType.TOOL_SUGGESTOR)

    orchestrator = AgentOrchestrator(
        narrative_agent=narrative_agent,
        combat_agent=combat_agent,
        summarizer_agent=self.summarizer_agent,
        combat_service=self.combat_service,
        event_bus=self.event_bus,
        game_service=self.game_service,
        metadata_service=self.metadata_service,
        conversation_service=self.conversation_service,
        agent_lifecycle_service=self.agent_lifecycle_service,
        tool_suggestor_agent=tool_suggestor_agent,  # NEW
        context_service=self.context_service,  # NEW - moved from agents
    )
    return AIService(orchestrator)
```

---

## Phase 4: System Prompt Enhancements (Day 10)

**Goal:** Enhance prompts in JSON files with tool usage guidance.

### 4.1 Enhance NPC System Prompts

**Files:** `data/agents/npc_individual.json`, `data/agents/npc_puppeteer.json`

Update `system_prompt` field to include:
- Clear tool categories (Quest Tools, Inventory Tools, Location Tools)
- When to use each tool type
- Tool guidelines (when to use vs. not use)
- Note about tool suggestions being advisory

Add TODO comment for future examples:
```
<!-- TODO: Add concrete examples of tool usage patterns -->
```

### 4.2 Add Tool Suggestion Section

**Files:** `data/agents/narrative.json`, `data/agents/combat.json`

Add section to end of `system_prompt`:
```
## Tool Suggestions
If tool suggestions appear in your context, they are advisory hints based on game state.
Review them carefully and use your judgment. Suggestions help you remember available tools.
```

---

## Phase 5: Party-Aware Context Sharing (Day 11)

**Goal:** NPCs in party see narrative messages for better context.

### 5.1 Update Message Converter Service

**File:** `app/services/ai/message_converter_service.py`

Update `to_pydantic_messages()` signature (full migration, no optional params):
```python
def to_pydantic_messages(
    messages: list[Message],
    agent_type: AgentType,
    game_state: GameState,
    npc_id: str,  # Required. Use "" for non-NPC agents
) -> list[ModelMessage]:
```

Update logic:
```python
allowed_agent_types = {agent_type}

# For Narrative agent: include NPC messages
if agent_type is AgentType.NARRATIVE:
    allowed_agent_types.add(AgentType.NPC)

# For NPC agent: include Narrative messages ONLY if THIS specific NPC is in party
if agent_type is AgentType.NPC and npc_id:
    if npc_id in game_state.party.member_ids:
        allowed_agent_types.add(AgentType.NARRATIVE)

# ... rest of filtering logic
```

**Rationale:** Only party member NPCs should see narrative messages for context. Non-party NPCs remain isolated.

### 5.2 Update All Agent Call Sites

**File:** `app/agents/npc/base.py`

Update `_build_message_history()` method:
```python
def _build_message_history(self, game_state: GameState) -> list[ModelMessage]:
    return self.message_converter.to_pydantic_messages(
        messages=game_state.conversation_history,
        agent_type=AgentType.NPC,
        game_state=game_state,
        npc_id=self._active_npc.instance_id,  # NEW: Pass specific NPC ID
    )
```

**File:** `app/agents/narrative/agent.py`

Update message history call:
```python
message_history = self.message_converter.to_pydantic_messages(
    messages=game_state.conversation_history,
    agent_type=AgentType.NARRATIVE,
    game_state=game_state,
    npc_id="",  # Not needed for narrative agent
)
```

**File:** `app/agents/combat/agent.py`

Update message history call (same pattern):
```python
message_history = self.message_converter.to_pydantic_messages(
    messages=game_state.conversation_history,
    agent_type=AgentType.COMBAT,
    game_state=game_state,
    npc_id="",  # Not needed for combat agent
)
```
---

## Phase 6: Testing & Validation (Days 13-15)

**Goal:** Comprehensive testing of all components.

### 6.1 Unit Tests

Create test files:

**`tests/unit/services/ai/tool_suggestion/test_heuristic_rules.py`**
- Test each rule class individually
- Test pattern matching (positive and negative cases)
- Test confidence calculation
- Test applicable_agents filtering

**`tests/unit/services/ai/tool_suggestion/test_tool_suggestion_service.py`**
- Test suggestion generation
- Test confidence filtering
- Test deduplication
- Test max_suggestions limit
- Test format_for_prompt()

**`tests/unit/agents/test_tool_suggestor_agent.py`**
- Test suggest_tools_for_agent()
- Test different agent types
- Test logging

**`tests/unit/models/test_agent_config.py`**
- Test AgentConfig validation
- Test ModelConfig validation
- Test RuleConfig validation
- Test invalid configs raise errors

**`tests/unit/services/ai/test_config_loader.py`**
- Test loading valid configs
- Test loading invalid configs (should raise)
- Test file not found errors

### 6.2 Integration Tests

**`tests/integration/test_tool_suggestions_flow.py`**
- Test full flow: user message → orchestrator → suggestions → agent
- Verify suggestions appear in agent context
- Verify agents can use suggestions
- Test multiple agent types (narrative, combat, npc)

**`tests/integration/test_full_suggestion_flow.py`** (NEW - PRIORITY)
- Test complete end-to-end flow:
  1. User input → AgentOrchestrator
  2. Orchestrator determines agent type via agent_router
  3. Orchestrator calls ToolSuggestorAgent with structured prompt
  4. ToolSuggestorAgent returns suggestions
  5. Orchestrator builds base context via ContextService
  6. Orchestrator enriches context with suggestions
  7. Target agent receives enriched context and processes
- Verify tool suggestions actually influence agent behavior
- Test with scenarios where tools should/shouldn't be called
- Measure suggestion accuracy (suggested tool was actually called)

**`tests/integration/test_config_driven_agents.py`**
- Test agents load prompts from JSON
- Test changing config file changes agent behavior
- Test startup validation catches bad configs

### 6.3 Manual Testing

Create script `scripts/test_tool_suggestions.py`:
- Load game state
- Test various user messages
- Print suggestions generated
- Verify they make sense

Test scenarios:
- "I accept the quest" → should suggest start_quest
- "Here's 50 gold" → should suggest modify_inventory
- "I attack the goblin" (in combat) → should suggest next_turn
- "I want to rest" → should suggest short_rest/long_rest

---

## Breaking Changes Summary

**⚠️ CRITICAL:** This implementation includes several breaking changes. Full migration required - no backward compatibility.

### API Changes

1. **BaseAgent.process() signature** ([app/agents/core/base.py](app/agents/core/base.py:26))
   - **Before:** `process(prompt, game_state, stream=True)`
   - **After:** `process(prompt, game_state, context, stream=True)`
   - **Impact:** ALL agents (Narrative, Combat, Summarizer, NPC)

2. **MessageConverterService.to_pydantic_messages() signature** ([app/services/ai/message_converter_service.py](app/services/ai/message_converter_service.py:19))
   - **Before:** `to_pydantic_messages(messages, agent_type)`
   - **After:** `to_pydantic_messages(messages, agent_type, game_state, npc_id)`
   - **Impact:** All agents that call this method (3 call sites)

3. **AgentFactory API** ([app/agents/factory.py](app/agents/factory.py:52))
   - **Before:** `@classmethod` methods with many parameters
   - **After:** Instance methods with dependencies injected via `__init__`
   - **Impact:** Container must instantiate factory, tests must update

### Dependency Changes

1. **Agents no longer depend on IContextService**
   - Removed from: NarrativeAgent, CombatAgent, BaseNPCAgent, SummarizerAgent
   - Context now built by orchestrator and injected

2. **AgentFactory gains new dependencies**
   - New: `AgentConfigLoader`, `ToolSuggestionService`
   - All service dependencies moved from method params to `__init__`

3. **AgentOrchestrator gains new dependencies**
   - New: `ToolSuggestorAgent`, `IContextService`

---

## Documentation Updates

### Update CLAUDE.md

Add section on Agent Configuration System:
- Explain data-driven approach
- Document file locations
- Show how to edit prompts
- Show how to add heuristic rules
