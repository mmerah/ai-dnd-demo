# Plan: Full Migration to Dynamic Instances (Character/NPC/Scenario) with Compute and Level-Up Basics

This plan replaces all legacy, precomputed storage with a clean instance-based architecture and a compute layer. It fully migrates saves and API to instances, adds ScenarioInstance, and auto-materializes NPCs on location change. Performance is not a constraint.

## Objectives
- Separate static templates (catalog: CharacterSheet, NPCSheet, Scenario) from dynamic runtime state (instances).
- Remove precomputed values from templates; compute derived values at runtime from base choices + rules and store only dynamic state in instances.
- Introduce CharacterInstance, NPCInstance, ScenarioInstance; wire GameState around them.
- Fully replace save format; delete existing saves; no legacy support.
- Provide minimal but correct computation and level-up logic so instances have coherent values (HP, modifiers, proficiency, slots, AC, skills/saves, attacks, spell DC/attack).
- Keep pre-game selection of characters (list of CharacterSheet templates) and scenarios (Scenario templates).

## Model Refactor (templates vs instances)
- Templates (static, under `data/`):
  - CharacterSheet (trimmed to base identity and choices; remove dynamic runtime fields like current HP, AC, conditions, spell slots).
  - NPCSheet (scenario-facing identity + reference to template character; no dynamic state).
  - Scenario (world definition; no dynamic state).
- Instances (dynamic, under `app/models/instances/`):
  - CharacterInstance
    - identity: `instance_id`, `template_id`, timestamps, metadata (`content_pack`, `origin_scenario` optional).
    - base choices snapshot: race_index/subrace_index, class/subclass index, background/alignment, base ability scores, starting known spells, selected skills/languages, selected fighting style/subclass choices, etc. (copied from template at creation, then owned by the instance).
    - dynamic state only: level, XP, current HP, current hit dice, conditions, exhaustion, inspiration, inventory/currency/equipment, spell slots, prepared spells, temporary HP/effects, attitude/notes/tags.
  - NPCInstance
    - identity: `instance_id`, `scenario_npc_id`, timestamps, attitude/notes/present.
    - character: CharacterInstance (created from NPCSheet character template).
  - ScenarioInstance
    - identity: `instance_id`, `template_id` (scenario id), timestamps, notes/tags.
    - dynamic progression: current act id/index, visited locations, per-location state (danger level, encounters completed, secrets discovered, effects), active/complete quests, quest flags, discovered items, spawned monsters/NPCs.

Note: All dynamic fields move from templates (and current GameState fields) to the relevant Instance. Templates remain single source of truth for definitions; Instances carry evolving state and player/NPC choices.

## Compute Layer (derived values at runtime)
Introduce a minimal `CharacterComputeService` that, given a CharacterInstance and catalogs (class/race/features/items/spells):
- Calculates: ability modifiers; proficiency bonus (by level); saving throws (class proficiencies + mods + proficiency); skill modifiers (proficiencies/expertise + mods + proficiency); AC (armor/shield + DEX cap rules + features like Defense); initiative; attacks (to-hit/damage strings from equipped weapons and stats); spell save DC (8 + prof + ability mod) and spell attack bonus; spell slot table (from class and level; stored in instance for consumption and persistence); senses/speed from race/subrace and equipment; languages.
- Returns a `ComputedCharacterView` used by API/Context when rendering. No duplicate storage of derived numbers; compute fresh when needed.

This supports removing precomputed `proficiency_bonus`, `saving_throws`, `skills`, `armor_class`, `attacks`, `spell slots` etc. from templates. Instances store only the mutable subset (e.g., current HP, current slots), while tables and totals come from compute + class progressions.

## Level-Up (minimal service)
`LevelProgressionService` (single-class only for this pass; TODO: multiclass support):
- Increments level and updates: hit dice total, HP maximum (+ rolled or average + CON mod), spell slot totals (by class progression), new features indices unlocked (returning required choices), proficiency bonus (from compute), known spells changes (choice list produced; apply when selected).
- Produces a `LevelUpPlan` detailing new features/choices; applies updates to CharacterInstance (XP, level, HP changes, slots totals/current as appropriate) once choices resolved.

## GameState Redesign
- Replace embedded legacy types with instances:
  - `character: CharacterInstance` (was CharacterSheet)
  - `npcs: list[NPCInstance]` (was NPCSheet)
  - Add `scenario: ScenarioInstance` (replaces scattered `scenario_id`, `current_location_id`, quest flags, location_states; migrate these into the ScenarioInstance structure)
- Keep: conversation history, game events, combat state (but link to instances by name/id), monsters list (unchanged for now but may become MonsterInstance later).

## Auto-materialize NPCs on Location Change
- When changing location, load the scenario template location, resolve `npc_ids`, and materialize corresponding `NPCInstance` objects into `game_state.npcs` (ensure deduping). Presence controlled by `present` field in each NPCInstance.

## Save Format (full replacement)
- Purge existing `saves/` (delete legacy). New layout per save:
  - `metadata.json` (game_id, created_at/last_saved, agent info, etc.)
  - `character_instance.json`
  - `scenario_instance.json`
  - `npcs/` → `<i>-<safe-name>.json` (NPCInstance)
  - `monsters/` (unchanged for now)
  - `conversation_history.json`, `game_events.json`
  - `combat.json` when active
- No legacy readers/wrappers. On startup (or first run of migration), wipe `saves/` directory.

## API Changes
- `/characters` and `/characters/{id}`: still return CharacterSheet templates (for pre-game selection). We’ll ensure templates are compatible (contain base identity/choices), but derived numbers are not required.
- `/scenarios` and `/scenarios/{id}`: still return Scenario templates (for pre-game selection).
- `/game/new`: accepts character_id and scenario_id, creates an instance-based GameState.
- `/game/{id}` and `/games`: return the new GameState shape with instances. For rendering, the server may also expose a computed view endpoint (optional): `/game/{id}/character/computed` returning `ComputedCharacterView`.

## Services Refactor
- CharacterService: remains catalog/template service for characters. Add helpers to create CharacterInstance from a CharacterSheet template.
- ScenarioService: remains template loader. Add `materialize_npc_instance` and helpers to seed ScenarioInstance (acts, starting location state).
- GameService:
  - Initialize: create CharacterInstance, ScenarioInstance; set starting location; auto-materialize NPCs for the starting location.
  - Change location: update ScenarioInstance current location and auto-materialize NPCInstances for that location.
- SaveManager: read/write only new instance files; no legacy codepaths.
- ContextService: consume instances; when needed, call compute service to render derived numbers.
- New services:
  - CharacterComputeService
  - LevelProgressionService

## Data Migration (code + content)
- Repo-wide cleanup: strip derived/dynamic fields from all `data/characters/*.json` templates and adjust the CharacterSheet model accordingly. Remove (non-exhaustive list): `proficiency_bonus`, `saving_throws`, `skills`, `armor_class`, `initiative`, `speed`, `hit_points`, `hit_dice`, `attacks`, `conditions`, `exhaustion_level`, `inspiration`, and in `spellcasting` remove `spell_save_dc`, `spell_attack_bonus`, and `spell_slots`. Keep only base identity and choices: name/id, race/subrace, class/subclass, background/alignment, base abilities, initial known/prepared spells (seed only), selected skills/languages/features, and starting inventory/equipment.
- Known/prepared spells: exist in templates only as initial seeds; after game creation they live exclusively on the CharacterInstance.
- NPCSheet remains a scenario asset but must not carry dynamic fields; ensure scenario NPC JSONs follow this rule.
- Purge `saves/` directory (delete all legacy saves) as part of migration.
- Implement and run a normalization script to rewrite character templates and validate with repositories; commit updated JSONs.

## Implementation Steps
1) Models (instances)
  - Add `app/models/instances/character_instance.py`, `npc_instance.py`, `scenario_instance.py`; include metadata, notes/attitude; Pydantic models.
2) Models (templates tightening)
  - Update CharacterSheet: remove dynamic runtime fields across the board (HP, hit dice, AC, initiative, speed, proficiency bonus, saves, skills, attacks, conditions, inspiration, exhaustion, spell slots and computed spell stats). Inventory remains as starting equipment; it seeds the instance’s inventory at creation.
  - Confirm NPCSheet carries only identity + character template reference; no runtime state.
3) Compute layer
  - Add `CharacterComputeService` with methods to derive: modifiers, proficiency, saves, skills, AC, initiative, attacks, spell DC/attack, slot totals by class+level. Use repos: classes, subclasses, races, items, weapon properties, skills, spells, features/traits as needed. Provide guardrails (clear errors) for missing data.
  - Define `ComputedCharacterView` Pydantic model for API/Context consumption.
4) Level-up
  - Add `LevelProgressionService` with minimal logic to increment level, compute new HP/slots, and produce choices. Integrate with GameService endpoint(s) or tools.
5) GameState & services
  - Refactor GameState to embed CharacterInstance, NPCInstance list, ScenarioInstance. Remove scattered scenario fields (migrate into ScenarioInstance).
  - GameService.initialize_game creates instances, seeds starting location, auto-NPCs, saves.
  - Change location flow creates/updates NPCInstances and scenario location state.
6) SaveManager
  - Write/read `character_instance.json`, `scenario_instance.json`, and `npcs/*.json`. Update list+load routines accordingly.
  - Implement utility to purge old `saves/`.
7) Handlers/Tools
  - Update `CharacterHandler`, `InventoryHandler`, `LocationHandler`, `Time` rest logic to mutate instances only.
  - Use compute service for any derived values needed during handling (e.g., AC for display).
8) API & container wiring
  - Wire new services in `container.py`. Update API response models and routes to return instance-based GameState and, optionally, computed views.
9) ContextService
  - Update to use instances and computed view for display numbers.
10) Docs
  - Add `docs/instances.md` and update `README.md` to explain templates vs instances and compute.

## Acceptance Criteria
- Saves contain only instance files (character_instance.json, scenario_instance.json, npc instances), with no legacy files present. Existing `saves/` are cleared.
- GameState contains CharacterInstance, ScenarioInstance, NPCInstances; location change auto-materializes location NPCs into `game_state.npcs`.
- Derived character values are computed at runtime; templates do not store runtime numbers.
- Minimal level-up adjusts level, HP, slots, and outputs choices to apply.
- `/characters` still lists templates for pre-game selection; `/game/*` endpoints return the new shapes.
 - Character templates in `data/characters` are cleaned of derived fields and committed; validation enforces absence of dynamic fields.

## Clarifying Questions
- None beyond naming preferences for any new endpoints (e.g., a computed character view), otherwise proceeding as specified.
