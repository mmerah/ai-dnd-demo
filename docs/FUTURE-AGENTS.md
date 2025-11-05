# Future Agents — Design Notes and Integration Hooks

This document captures postponed agents, their intended value, integration points, and risks. They can be implemented incrementally once NPC agents and memory are stable.

## DirectorAgent (Pacing & Meta-Narrative)
- Purpose: Adjust story pacing, dramatic tension, and difficulty.
- Inputs: GameState, recent conversation/game events, player profile (optional).
- Outputs: Advisory directives to Narrative/Combat or content creators (e.g., “introduce complication”, “foreshadow X”).
- Integration:
  - Runs before/after a narrative turn; provides guidance strings injected into NarrativeAgent context as annotations (not hard constraints).
  - Can suggest encounters but should not execute tools directly (governance layer only).
- Risks: Oversteering the narrative; mitigate by advisory-only outputs with clear precedence (Narrative agent remains sovereign).

## EnvironmentAgent (World Simulation)
- Purpose: Simulate world/NPC background changes over time to make the world feel alive.
- Triggers: On time progression (short/long rest, advance_time) or explicit ticks (day boundaries).
- Actions:
  - Update `LocationState` (effects, danger shifts) and NPC locations/states.
  - Create world memory entries summarizing simulated changes.
- Integration:
  - Called via an orchestrator hook after time changes; mutates state via existing services (LocationService as needed).
  - Uses MemoryService to record world updates.
- Risks: Complexity/overhead; keep deterministic and rate-limited; initial simplified rules only.

## PlayerPsychologistAgent (Playstyle Analysis)
- Purpose: Tailor experience to the player’s style.
- Inputs: GameEvent log, conversation history (rates of combat vs dialogue, risk-taking, thoroughness).
- Outputs: Advisory profile (e.g., “combat-forward, low exploration”) for the Director/Creator agents.
- Integration: Writes profile to ScenarioInstance tags or a dedicated analytics store; referenced by DirectorAgent.
- Risks: Privacy/overreach; keep analysis coarse and local; opt-in.

## Creator Agents (ItemCreator, EncounterDesigner)
- Purpose: On-the-fly content generation for sandbox/side content.
- Calls: Invoked explicitly by NarrativeAgent when player seeks new content, or by DirectorAgent as advisory.
- Outputs: Structured definitions (ItemDefinition, Encounter) for review and commit.
- Integration:
  - Propose content to NarrativeAgent which then confirms with the player before committing via tools (add item, spawn/free-roaming).
  - Store generated content in a per-game “homebrew” registry for determinism.
- Risks: Canon creep and balance issues; require explicit confirmation flow.

## ArtDirectorAgent (Multi-Modal)
- Purpose: Generate illustrative assets (images/ambience) to enhance immersion.
- Triggers: NarrativeAgent marks a “vista”/“scene” or explicit DM command.
- Outputs: Image URLs or audio cues via SSE for the frontend.
- Integration: Listens to broadcast queue or explicit calls; does not mutate game state; caches assets with content-addressable keys.
- Risks: External service reliability; wrap with retries and graceful degradation.

## Utility & Governance Notes
- All background/advisory agents should produce suggestions or annotations, not direct state mutations (leave tool execution to core agents/NPCs with explicit confirmation when needed).
- Extend `ContextService` with minimal builders per agent to avoid bloated prompts.
- Keep “one agent produces user-visible output per turn” to preserve clarity.

## Additional Agent Ideas

### LorekeeperAgent (Canon & Continuity)
- Purpose: Enforce internal consistency across sessions and acts; catch contradictions.
- Inputs: Scenario canon, world_memories, npc_memories.
- Outputs: Annotations for agents (e.g., “Tom previously promised a discount”) and warnings on conflicts.
- Integration: Pre-flight check for Narrative/NPC turns; advisory only.

### FactionReputationAgent (Social Systems)
- Purpose: Track factions, reputations, and standing modifiers; influence NPC attitudes.
- Inputs: Choices, NPC memories.
- Outputs: Reputation deltas, attitude suggestions to NPC agents.
- Integration: Writes a faction state map to ScenarioInstance; read by NPC/Narrative agents.

### RulesArbiterAgent (5e Rulings)
- Purpose: Provide rulings for edge cases and optional rules references.
- Inputs: Current action description, character stats.
- Outputs: Advisory rulings (DCs, advantage, improvised checks) for Narrative/Combat agents.
- Integration: Called synchronously by Narrative/Combat for tough calls; no direct tool use.

### EncounterBalancerAgent (CR & Rewards)
- Purpose: Suggest balanced encounters and rewards based on party level and resources.
- Inputs: Character level, inventory power, recent combat outcomes.
- Outputs: Encounter templates, XP/treasure suggestions.
- Integration: Feeds Narrative/Director or Creator agents; requires explicit confirmation before spawning/adding.

### TacticalAdvisorAgent (Enemy AI Hints)
- Purpose: Provide higher-level tactics to the CombatAgent (focus fire, terrain usage).
- Inputs: CombatState, participant stat blocks, conditions.
- Outputs: Short tactical directives; optional move targets.
- Integration: Advisory to CombatAgent each round start; no direct tool calls.

### WeatherAndCalendarAgent (Atmosphere & Timing)
- Purpose: Simulate weather, moon phases, festivals; enrich narrative hooks.
- Inputs: GameTime, location biome/altitude, season.
- Outputs: Location effects (e.g., visibility), narrative annotations, world memory entries.
- Integration: Triggered on time changes; updates LocationState effects via LocationService.

### MemoryCuratorAgent (Summaries & Pruning)
- Purpose: Periodically merge older memories into condensed summaries; tag highlights.
- Inputs: All memory scopes; player progress.
- Outputs: Curated canonical memory entries, pruning plan.
- Integration: Invoked out of band (menu action or save-time hook); uses MemoryService APIs.

### ShopkeeperEconomyAgent (Trade & Pricing)
- Purpose: Generate dynamic shop inventories, prices, and supply/demand events.
- Inputs: Region, player purchases.
- Outputs: Inventory lists and price multipliers per location.
- Integration: Updates NPC shop states; Narrative pulls to describe offers.

### PuzzleMasterAgent (Riddles & Challenges)
- Purpose: Create solvable puzzles tied to scenario themes; track hints/state.
- Inputs: Scenario motifs, location secrets.
- Outputs: Puzzle definitions, hints, and validation logic.
- Integration: Narrative requests a puzzle; agent returns structured puzzle with solution; tools update state on solve.

### SessionPrepAgent (GM Assistant)
- Purpose: Prepare upcoming scenes: recap, beats, likely branches, props.
- Inputs: World/NPC memories, current act, player trends.
- Outputs: A brief prep packet; optional frontloaded summaries.
- Integration: Developer/DM utility; not invoked during player turns.

### AccessibilityAgent (Narrative Simplifier)
- Purpose: Provide simplified versions of outputs (concise, dyslexia-friendly), optional alt text for images.
- Inputs: Current narrative/NPC lines.
- Outputs: Alternative text streams.
- Integration: Frontend-selectable mode; no game state mutations.

### LocalizationAgent (Multi-language)
- Purpose: Translate outputs while preserving game terms and proper nouns.
- Inputs: Narrative/NPC lines; term glossary.
- Outputs: Localized text.
- Integration: Optional per-client setting; caches translations per message hash.

### HomebrewImportAgent (Data Ingestion)
- Purpose: Validate and import user-provided JSON/YAML content (items, monsters).
- Inputs: Files or text; schema definitions.
- Outputs: Cleaned, normalized content packs with validation reports.
- Integration: Offline/DM tool; registers content via repository factory.

## Phased Rollout
1) Stabilize NPC agents + memory.
2) Add EnvironmentAgent with simple day-tick rules and world memory writes.
3) Introduce DirectorAgent (advisory-only) and a tiny CreatorAgent for side tasks.
4) Explore PlayerPsychologist profile feeding Director/Creator.
5) Optional: ArtDirectorAgent for multi-modal enrichment.
