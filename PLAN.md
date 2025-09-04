# Plan: Full Migration to Dynamic Instances (Character/NPC/Scenario) with Compute and Level-Up Basics

This plan replaces all legacy, precomputed storage with a clean instance-based architecture and a compute layer. It fully migrates saves and API to instances, adds ScenarioInstance, and auto-materializes NPCs on location change. Performance is not a constraint. We will apply SOLID and DRY principles across services and models.

## Objectives
- Separate static templates (catalog: CharacterSheet, NPCSheet, Scenario) from dynamic runtime state (instances).
- Remove precomputed values from templates; compute derived values at runtime from base choices + rules and store only dynamic state in instances.
- Introduce CharacterInstance, NPCInstance, ScenarioInstance; wire GameState around them.
- Fully replace save format; delete existing saves; no legacy support.
- Provide minimal but correct computation and level-up logic so instances have coherent values (HP, modifiers, proficiency, slots, AC, skills/saves, attacks, spell DC/attack).
- Keep pre-game selection of characters (list of CharacterSheet templates) and scenarios (Scenario templates).

## Model Refactor (templates vs instances)
- Templates (static, under `data/`):
  - CharacterSheet (trimmed to base identity and choices; remove dynamic/derived runtime fields like HP/Hit Dice, AC/initiative/speed, proficiency bonus, saving throws, skill totals, attacks, conditions, inspiration/exhaustion, spell slots, spell save DC/attack bonus).
  - NPCSheet (scenario-facing identity and still embeds a CharacterSheet template inline; the embedded character is also trimmed as above and carries no dynamic state).
  - Scenario (world definition; no dynamic state).
- Instances (dynamic, under `app/models/instances/`):
  - CharacterInstance
    - identity: `instance_id` (stable across saves), `template_id`, timestamps, metadata (`content_pack`, `origin_scenario` optional).
    - embeds a trimmed `CharacterSheet` snapshot (DRY). Dynamic/derived fields are removed from the sheet in the trimming phase.
    - instance-only metadata/notes/tags; dynamic state lives on the instance after trimming the sheet in later phases.
  - NPCInstance
    - identity: `instance_id`, `scenario_npc_id`, timestamps, attitude/notes/present.
    - character: CharacterInstance (created from NPCSheet character template).
  - ScenarioInstance
    - identity: `instance_id` (stable), `template_id` (scenario id), timestamps, notes/tags.
    - dynamic progression/state unified here: current act index, `current_location_id`, visited locations, per-location state (danger level, encounters completed, secrets discovered, effects), active/complete quests, quest flags, discovered items, spawned monsters/NPCs.

Note: All dynamic fields move from templates (and current GameState fields) to the relevant Instance. Templates remain single source of truth for definitions and choices; Instances carry evolving state and player/NPC selections.

## Compute Layer (derived values at runtime)
Introduce a minimal `CharacterComputeService` (via an interface) that, given the core models (CharacterInstance/CharacterSheet) and catalogs via repository interfaces:
- Calculates: ability modifiers; proficiency bonus (by level); saving throws (class proficiencies + mods + proficiency); skill modifiers; AC (and later equipment rules); initiative; attacks (later); spell save DC and spell attack bonus. No view-only models; returns core models/values (DRY).
- Spell slots: derive max slot totals from class progression (later). Persist only current slots; compute totals on demand.

This supports removing precomputed `proficiency_bonus`, `saving_throws`, `skills`, `armor_class`, `attacks`, `spell slots`, and `spell_save_dc/attack` from templates. Instances store only the mutable subset (e.g., current HP, current slots), while totals come from compute + class progressions.

## Level-Up (minimal service)
`LevelProgressionService` (single-class only; multiclassing out of scope):
- Increments level and updates: hit dice total, HP maximum (+ rolled or average + CON mod), slot totals (progression or pact magic), new features unlocked (returning required choices), proficiency bonus (from compute), known spells changes (choice list; apply when selected).
- Produces a `LevelUpPlan` detailing new features/choices; applies updates to CharacterInstance (XP, level, HP changes, slots current adjusted) once choices resolved.

## GameState Redesign
- Replace embedded legacy types with instances:
  - `character: CharacterInstance` (was CharacterSheet)
  - `npcs: list[NPCInstance]` (was NPCSheet)
  - Add `scenario: ScenarioInstance` (moves `scenario_id`, `current_location_id`, quest flags, `location_states`, act progress, `active_quests`, `completed_quest_ids` into ScenarioInstance)
- Keep: conversation history, game events, combat state (but link to instances by name/id), monsters list (unchanged for now but may become MonsterInstance later).

## Auto-materialize NPCs on Location Change
- When changing location, load the scenario template location, resolve `npc_ids`, and materialize corresponding `NPCInstance` objects into `game_state.npcs`.
- Dedup by `scenario_npc_id`; update `present` flag according to the location.

## Save Format (full replacement)
- New layout per save (folders for clarity):
  - `metadata.json` (game_id, created_at/last_saved, agent info, scenario summary)
  - `instances/`
    - `character.json` (CharacterInstance)
    - `scenario.json` (ScenarioInstance; includes location/quest state)
    - `npcs/` → `<npc-instance-id>.json` (NPCInstance)
  - `monsters/` (unchanged for now)
  - `conversation_history.json`, `game_events.json`
  - `combat.json` when active
- Instance IDs are stable across saves (generated once and persisted).
- No legacy readers/wrappers. Saves were purged manually already; no automatic deletion on startup.

## API Changes
- `/characters` and `/characters/{id}`: return trimmed CharacterSheet templates (identity + choices only).
- `/scenarios` and `/scenarios/{id}`: return Scenario templates (unchanged layout; scenario NPCs still embed trimmed CharacterSheet).
- `/game/new`: accepts character_id and scenario_id; creates an instance-based GameState.
- `/game/{id}` and `/games`: return the new instance-based GameState shape (breaking change for MVP). No compatibility endpoints planned.

## Services Refactor
- CharacterService: remains catalog/template service for characters. Add `create_instance_from_template(template) -> CharacterInstance` and validation helpers.
- ScenarioService: remains template loader. Add `materialize_npc_instance(scenario_id, npc_id) -> NPCInstance` and helpers to seed ScenarioInstance (acts, starting location state).
- GameService:
  - Initialize: create CharacterInstance, ScenarioInstance; set starting location; auto-materialize NPCs for the starting location; save with new structure.
  - Change location: update ScenarioInstance current location and auto-materialize/dedupe NPCInstances for that location.
- SaveManager: read/write only new instance files/folders; no legacy codepaths. Keep responsibilities focused (SRP).
- ContextService: consume instances; call compute service for derived values when needed (AI context). No extra endpoints for frontend MVP.
- New services:
  - CharacterComputeService
  - LevelProgressionService

## Data Migration (code + content)
- Repo-wide cleanup: strip derived/dynamic fields from all `data/characters/*.json` templates and adjust the CharacterSheet model accordingly. Remove (non-exhaustive list): `proficiency_bonus`, `saving_throws`, `skills` totals, `armor_class`, `initiative`, `speed`, `hit_points`, `hit_dice`, `attacks`, `conditions`, `exhaustion_level`, `inspiration`, and in `spellcasting` remove `spell_save_dc`, `spell_attack_bonus`, and `spell_slots`. Keep only base identity and choices: name/id, race/subrace, class/subclass, background/alignment, base abilities, initial known/prepared spells (seed only), selected skills/languages/features, and starting inventory/equipment.
- Known/prepared spells: exist in templates only as initial seeds; after game creation they live exclusively on the CharacterInstance.
- Scenario NPC JSONs continue to embed a CharacterSheet, but that embedded sheet is also trimmed as above (no dynamic fields).
- Saves were purged manually already.
- Implement and run a normalization script to rewrite character templates and scenario NPC embedded characters; validate with repositories; commit updated JSONs.

## Implementation Steps
1) Models (instances)
  - Add `app/models/instances/character_instance.py`, `npc_instance.py`, `scenario_instance.py`; include metadata, notes/attitude; Pydantic models.
2) Models (templates tightening)
  - Update CharacterSheet: remove dynamic runtime fields across the board (HP, hit dice, AC, initiative, speed, proficiency bonus, saves, skills, attacks, conditions, inspiration, exhaustion, spell slots and computed spell stats). Inventory remains as starting equipment; it seeds the instance’s inventory at creation.
  - Confirm NPCSheet carries only identity + character template reference; no runtime state.
3) Compute layer
  - Add `CharacterComputeService` with methods to derive: modifiers, proficiency, saves, skills, AC, initiative, attacks, spell DC/attack, slot totals by class+level. Use repos: classes, subclasses, races, items, weapon properties, skills, spells, features/traits as needed. Provide guardrails (clear errors) for missing data.
  - No view-only models. Expose compute results as core models/values (e.g., `AbilityModifiers`, dicts for saves/skills).
4) Level-up
  - Add `LevelProgressionService` with minimal logic to increment level, compute new HP/slots, and produce choices. Integrate with GameService endpoint(s) or tools.
5) GameState & services
  - Refactor GameState to embed CharacterInstance, NPCInstance list, ScenarioInstance. Remove scattered scenario fields (migrate into ScenarioInstance).
  - GameService.initialize_game creates instances, seeds starting location, auto-NPCs, saves.
  - Change location flow creates/updates NPCInstances and scenario location state.
6) SaveManager
  - Write/read `instances/character.json`, `instances/scenario.json`, and `instances/npcs/*.json`. Update list+load routines accordingly.
7) Handlers/Tools
  - Update `CharacterHandler`, `InventoryHandler`, `LocationHandler`, `Time` rest logic to mutate instances only.
  - Use compute service for any derived values needed during handling (e.g., AC for display).
8) API & container wiring
  - Wire new services in `container.py`. Update API response models and routes to return instance-based GameState.
9) Frontend (MVP)
  - Update the frontend to consume the new instance-based GameState (no backend compatibility endpoints).
10) Docs
  - Add `docs/instances.md` and update `README.md` to explain templates vs instances and compute.

## Acceptance Criteria
- Saves contain only instance files/folders (`instances/character.json`, `instances/scenario.json`, `instances/npcs/*.json`), with no legacy files present.
- GameState contains CharacterInstance, ScenarioInstance, NPCInstances; location change auto-materializes location NPCs (deduped) into `game_state.npcs` and toggles presence.
- Derived character values are computed at runtime; templates do not store derived/runtime numbers. Instances store only mutable state (e.g., current slots).
- Minimal level-up adjusts level, HP, slots, and outputs choices to apply.
- `/characters` still lists templates for pre-game selection; `/game/*` endpoints return the new instance-based shapes (breaking change for MVP).
- Character templates in `data/characters` and embedded scenario NPC characters are cleaned of derived fields and committed; validation enforces absence of dynamic fields.
- Instance IDs are stable across saves.

## Clarifications (confirmed)
- Saves structure: keep `metadata.json`, `conversation_history.json`, `game_events.json`, `monsters/`, `quests/`, and `combat.json` alongside the new `instances/` folder. “Only” applies to replacing `character.json` and `npcs/` with `instances/*`.
- Character template fields to keep: id, name, race/subrace, class/subclass, background, alignment, base ability scores, selected skills/languages/features/spells. Use explicit `starting_*` prefixed fields (e.g., `starting_level`, `starting_experience_points`, `starting_inventory`, `starting_currency`, `starting_spellcasting`) to seed instances. Move all dynamic/derived fields to the instance.
- NPC instances: `NPCInstance` embeds a full `CharacterInstance` (created from the NPC’s trimmed character template) and carries `scenario_npc_id`, `attitude`, `notes`, and `present`.
- Scenario instance: move `current_location_id`, `current_act_id`, `location_states`, `active_quests`, `completed_quest_ids`, and `quest_flags` from `GameState` into `ScenarioInstance`.
