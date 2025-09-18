# Agent Extension Plan — Focused on NPC Agents

This plan extends the agent architecture with NPC agents that add real value now, while keeping the system cohesive and SOLID. It integrates seamlessly with the orchestrator and the memory system defined in PLAN.md.

## Goals
- Enable natural, targeted dialogues with NPCs using explicit `@Name` and implicit addressing.
- Support multi-party dialogue (multiple NPCs replying, interleaved) and an optional dialogue mode across turns.
- Let major NPCs (party members, key figures) have individual, persistent minds; minor NPCs share a puppeteer.
- Allow NPC agents to use safe tools (quests, inventory, location) with guardrails.
- Preserve clean narrative handoff and correct conversation history so narrative context stays consistent.
- Integrate all relevant memories (npc/location/world) in NPC prompts.

## Agents Chosen (Now)
- IndividualMindAgent (major NPCs)
  - Dedicated, stateful agent per major NPC (party members, main villains).
  - Personality and continuity from `NPCSheet` + `NPCInstance` + memories.

- PuppeteerAgent (minor NPCs)
  - A single agent that role-plays any minor NPC using an injected persona.

Postponed agents are documented in FUTURE-AGENTS.md.

## Data & Model Changes
- AgentType
  - Add: `NPC` (single type for all NPC agents; not switching `active_agent`).

- NPC classification
  - Add `importance: Literal['major','minor']` on `NPCSheet` to designate individual vs puppeteer routing.

- Dialogue session state (GameState)
  - Add `dialogue_session`:
    - `active: bool`
    - `target_npc_ids: list[str]`
    - `started_at: datetime`
    - `last_interaction_at: datetime`
    - `mode: Literal['explicit_only','sticky']` (default: `explicit_only` → continue only if message keeps targeting NPCs)

- Conversation history (Message)
  - Extend `MessageRole` with `NPC`.
  - Add fields: `speaker_npc_id: str | None`, `speaker_npc_name: str | None`.
  - Keep existing metadata (location, npcs_mentioned, agent_type, combat tags).

- SSE events
  - Add `NPC_DIALOGUE` event with payload: `{ npc_id, npc_name, content, complete }`.

## Metadata and Routing
- MetadataService
  - Add `extract_targeted_npcs(message: str, game_state: GameState) -> list[str]`
    - Detect `@Name` tokens and implicit addressing (first-sentence name matching known NPCs at location).
    - Fail fast on unknown targets with a helpful error if none matched.

- Orchestrator (AgentOrchestrator)
  - Routing rules per turn:
    1) If combat is active: route to CombatAgent (unchanged).
    2) Else, compute `targeted_npcs = MetadataService.extract_targeted_npcs(user_message, game_state)`.
    3) If `targeted_npcs` non-empty → handle as NPC turn (dialogue):
       - Update/enter `dialogue_session` with these NPCs (mode: explicit_only).
       - Invoke NPC agents sequentially (see Multi-party Interleaving).
       - Record each NPC reply in conversation history with `MessageRole.NPC` and `speaker_npc_id`.
       - Broadcast `NPC_DIALOGUE` SSE events for each reply.
       - Do NOT generate narrative in the same turn.
    4) Else if `dialogue_session.active` and `mode=='explicit_only'` → exit dialogue session and continue with Narrative.
    5) Else route to NarrativeAgent (unchanged flow).
  - Logging: log which agent(s) handled the turn.

- Multi-party Interleaving
  - Determine speaking order by the order of `targeted_npcs` in the user message.
  - For each NPC, call its agent; append outputs in that order.
  - Keep one agent generating at a time (sequential), then broadcast and record in order.

## NPC Agent Design
- Common prompt design
  - Persona: built from `NPCSheet` (role, description, initial attitude) and `NPCInstance` (current attitude/notes), plus equipment where relevant.
  - Memory integration: include last N (default 3) entries from npc_memories (self), location_memories (current location), world_memories (scenario).
  - Scene context: current location summary and nearby NPCs (reuse existing builders: scenario, location, npcs_at_location, npc_detail as needed).
  - Conversation history: include recent dialogue turns involving the NPC(s) from `conversation_history` (filtered by `speaker_npc_id` and player lines).

- Allowed tools for NPC agents
  - Quests: `start_quest`, `complete_objective`, `complete_quest` (e.g., offers/updates when the player accepts or completes tasks).
  - Inventory: `modify_inventory` (giving/taking items when appropriate).
  - Location: `update_location_state`, `discover_secret`, `move_npc_to_location` (limited environmental interactions).
  - Guardrails: NPC agents do not call combat tools; attempting to do so results in a policy warning and blocked execution.

- Party Interjections (proactive)
  - A small service decides stochastically (e.g., 10–20% chance per player narrative turn) whether a party NPC interjects.
  - If chosen, invoke that NPC’s agent with a short “interjection” prompt and broadcast as `NPC_DIALOGUE`; record in history (MessageRole.NPC).

## Context Builders (Reuse + Small Additions)
- Reuse existing builders in `ContextService`:
  - Scenario, Location, NPCsAtLocation, NPCDetail, Quest, CurrentState, Inventory (if relevant), plus new memory builders from PLAN.md.
- Add `NPCPersonaContextBuilder` (small, focused):
  - Builds a profile for a given NPC for the agent prompt: role, goals, attitude, known relationships.

## Memory Integration
- Read: NPC agents include npc/location/world memories via context builders.
- Write: Follow PLAN.md — NPC memory entries are created on location exit (no immediate memory write after each turn).

## Conversation Recording
- Use `ConversationService.record_message` for the player prompt and for each NPC reply.
- Extend it to accept `speaker_npc_id` (and resolve/display name), and to set `MessageRole.NPC` for NPC replies.
- Ensure SaveManager persists the extended message fields (automatic with Pydantic).

## Lifecycle and Container
- AgentLifecycleService
  - Responsibilities:
    - `get_npc_agent(npc_instance: NPCInstance) -> BaseAgent`:
      - If `importance=='major'` → create/cache IndividualMindAgent bound to that NPC.
      - Else → return shared PuppeteerAgent configured for the target NPC per turn.
    - Release agents for NPCs that leave the player’s proximity (except party members).
  - Keep one cache per game.

- AgentFactory
  - Add creation for NPC agents:
    - `create_individual_mind_agent(...) -> IndividualMindAgent`
    - `create_puppeteer_agent(...) -> PuppeteerAgent`
  - Register no tools that the agent shouldn’t use; policy enforcement via tool decorator remains in effect.

- Container wiring
  - Add `agent_lifecycle_service`.
  - Register NPC agents (factory methods) and inject lifecycle service into orchestrator.
  - Add `MetadataService.extract_targeted_npcs`.
  - Extend `MessageService`/SSE models with `NPC_DIALOGUE`.

## Orchestrator Changes (Detailed)
- Extend `AgentOrchestrator.process`:
  - Detect targeted NPCs via MetadataService.
  - If any, produce NPC replies via lifecycle-managed agents and yield stream events for each reply (as narrative SSE + NPC_DIALOGUE SSE), then return.
  - Else follow existing narrative/combat routing including summarizer transitions.
- Dialogue mode (optional for later):
  - Phase 1 (MVP): use explicit targeting only — if subsequent turn lacks targets, exit dialogue.
  - Phase 2 (optional): `mode='sticky'` allows continuing dialogue without re-targeting; exit if the user types an exit phrase or targets none for N turns.

## Policy & Tool Guardrails
- Update `tool_handler` policy:
  - Allow `AgentType.NPC` for quest/inventory/location tools; block combat tool usage (like narrative block during combat, but broader).
  - Continue fail-fast with clear ToolErrorResult for blocked tools.

## SSE & Frontend
- Add `NPC_DIALOGUE` event; frontend renders NPC bubbles distinctly.
- Continue sending `GAME_UPDATE` when tools mutate state.
- Log which agent handled turn for dev transparency.

## Test Plan
- MetadataService
  - `extract_targeted_npcs` detects `@Name` and implicit addressing; fails fast on unknown names.
- Orchestrator
  - Routes NPC-addressed turns to NPC agents; multi-party interleaving order matches message order.
  - Falls back to Narrative when no targets and session inactive or after exit.
- NPC Agents
  - Produce responses reflecting persona + memory context.
  - Allowed tools execute; blocked ones yield policy warnings.
- Conversation Recording
  - NPC replies recorded with `MessageRole.NPC`, `speaker_npc_id` set.
- SSE
  - Emits `NPC_DIALOGUE` events with correct payload; narrative events unaffected.

## Rollout Steps
1) Extend enums/models (AgentType.NPC, MessageRole.NPC, message speaker fields, dialogue_session state, NPCSheet.importance).
2) Add MetadataService.extract_targeted_npcs.
3) Implement AgentLifecycleService + AgentFactory NPC methods.
4) Implement PuppeteerAgent + IndividualMindAgent (prompts, context usage, no combat tools).
5) Orchestrator routing for NPC dialogues (+ interleaving + party interjections hook).
6) Extend ConversationService/MessageService/SSE models.
7) Wire in Container; update tests.

## Non-Goals (Now)
- Creator/Director/Environment/Psychologist/Art agents — see FUTURE-AGENTS.md.
- Complex multi-turn dialogue session management (we start with explicit addressing only).
- NPC memory writes after each turn (handled on location exit).
