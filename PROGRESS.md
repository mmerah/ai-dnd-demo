# Migration to Instance-Based Architecture — Progress Log

This log documents every change completed so far, our design decisions, and the remaining steps — in enough detail for a new contributor to continue the work.

## Objectives
- Separate static templates (“sheets”) from dynamic runtime state (“instances”).
- Keep templates small and stable; move all gameplay state into instances.
- Remove derived values from templates and (eventually) compute them on demand.
- Make saves self-contained, explicit, and portable.

## Final Architecture (as of now)
- Template models (static):
  - CharacterSheet: identity + base choices; seeds instance via `starting_*` fields.
  - NPCSheet: scenario-level NPC metadata + embedded CharacterSheet; seeds instance via `initial_*` fields.
  - ScenarioSheet: the scenario/adventure template (replaces “Scenario” everywhere).
- Instance models (dynamic):
  - EntityState: shared runtime state for characters and NPCs (see below).
  - CharacterInstance: sheet: CharacterSheet + state: EntityState.
  - NPCInstance: sheet: NPCSheet + state: EntityState + runtime presentation (current_location_id, attitude, notes).
  - ScenarioInstance: sheet: ScenarioSheet + runtime progression (current_location_id, current_act_id), location_states, quests, flags.
- GameState: always holds CharacterInstance, NPCInstances, and ScenarioInstance (required). `current_location_id` is non-optional and uses the sentinel "unknown-location".
- Saves: `saves/<scenario-id>/<game-id>/instances/{character.json, scenario.json, npcs/*.json}` + `metadata.json`, `conversation_history.json`, `game_events.json`, `monsters/`, `combat.json`.
- SSE: broadcast full GAME_UPDATE only; no character-only SSE events.

## EntityState (runtime state, DRY)
- abilities: Abilities (current, dynamic).
- level, experience_points.
- hit_points (current, maximum, temporary), hit_dice (total, current, type).
- armor_class, initiative, speed.
- saving_throws: SavingThrows (typed model with STR/DEX/CON/INT/WIS/CHA fields).
- skills: list[EntitySkill] (index + value; index resolves to catalog Skill).
- attacks: list[Attack] (runtime weapon attacks).
- conditions: list[str], exhaustion_level: int, inspiration: bool.
- inventory: list[InventoryItem], currency: Currency | None.
- spellcasting: Spellcasting | None (current slots and prepared state).

## Completed Changes (files and details)

### Models
- app/models/character.py
  - CharacterSheet converted to template-only with `starting_*` fields:
    - starting_abilities, starting_level, starting_experience_points,
    - starting_inventory, starting_currency,
    - starting_spellcasting (no spell DC/attack stored).
  - Removed all deprecated runtime fields and behavior from CharacterSheet.
  - `CustomFeature` used for character-specific features.

- app/models/npc.py
  - NPCSheet is template-only; presentation fields renamed to seeds:
    - initial_dialogue_hints, initial_attitude, initial_notes.
  - Removed template-level `present` (runtime only on NPCInstance).

- app/models/scenario.py
  - Renamed the template model to ScenarioSheet; no alias.

- app/models/instances/entity_state.py
  - Added EntityState (see above), HitPoints, HitDice, Attack.
  - SavingThrows model added in app/models/ability.py.
  - EntitySkill added in app/models/skill.py.

- app/models/instances/character_instance.py
  - CharacterInstance has `sheet: CharacterSheet` and `state: EntityState`.

- app/models/instances/npc_instance.py
  - NPCInstance has `sheet: NPCSheet` and `state: EntityState`.
  - Runtime presentation: current_location_id: str, attitude: str | None, notes: list[str].
  - is_alive() checks `state.hit_points.current`.

- app/models/instances/scenario_instance.py
  - ScenarioInstance has `sheet: ScenarioSheet` (embedded for save portability),
    `current_location_id: str` (uses sentinel "unknown-location"), `current_act_id: str | None`, location_states, active_quests, completed_quest_ids, quest_flags, notes/tags.

- app/models/game_state.py
  - GameState now holds CharacterInstance, list[NPCInstance], list[Monster].
  - `scenario_instance: ScenarioInstance` is required and serves as the canonical place for scenario runtime state; `current_location_id` uses a non-optional sentinel.
  - Added explicit `-> LocationState` return type to `get_location_state` (fixed mypy --strict).

### Services & Loaders
- app/services/data/loaders/scenario_loader.py
  - Loads ScenarioSheet completely (locations, encounters, quests, progression, treasure guidelines).

- app/services/scenario/scenario_service.py
  - Returns ScenarioSheet; list_scenarios and getters updated; context string builder works with ScenarioSheet.

- app/services/character/character_service.py
  - Removed getattr usage; validates `starting_inventory` and `starting_spellcasting` directly.
  - Validates alignment, class/subclass, race/subrace, background, languages, traits, features, feats.

- app/services/game/game_service.py
  - Helper `_build_entity_state_from_sheet` (properly ordered) constructs EntityState from CharacterSheet `starting_*` fields:
    - abilities, level/XP, inventory/currency/spellcasting come from starting_*.
    - Derived values (AC, initiative, speed, saves, skills, attacks) defaulted sensibly until compute wiring.
  - initialize_game creates:
    - CharacterInstance with state seeded from CharacterSheet.
    - ScenarioInstance with embedded ScenarioSheet, current_location_id and current_act_id set.
    - Starting narrative and location state initialized.

- app/services/game/save_manager.py
  - Saves to `instances/character.json`, `instances/scenario.json`, `instances/npcs/*.json`.
  - Always saves/loads ScenarioInstance; if scenario.json missing in a legacy save, creates a minimal ScenarioInstance to keep invariants.
  - metadata.json includes `current_location_id` and `current_act_id` for convenience.

### Handlers & Context
- app/events/handlers/character_handler.py, inventory_handler.py, time_handler.py
  - Now mutate `game_state.character.state` (and `npc.state` where applicable).
  - Time handler uses instance abilities and level for rest mechanics.

- app/events/handlers/combat_handler.py
  - Uses `game_state.character.state.abilities.DEX` to compute player initiative.

- app/events/handlers/location_handler.py, quest_handler.py
  - Use ScenarioInstance for location/quest progression; `current_location_id` remains Optional.

- app/services/ai/context_service.py
  - Composes context from ScenarioSheet (via service), ScenarioInstance (runtime), and Character/NPC instances (sheet for identity, state for HP/AC/spells/inventory).

### API & SSE
- app/api/routes.py and app/models/sse_events.py
  - Routes and SSE models updated to ScenarioSheet.
  - SSE now broadcasts only full GAME_UPDATE; removed character-only SSE data and commands.

### Compute Layer (scaffolded)
- app/interfaces/services.py (ICharacterComputeService) & app/services/character/compute_service.py
  - compute_ability_modifiers(Abilities) -> AbilityModifiers
  - compute_proficiency_bonus(level: int) -> int
  - compute_saving_throws(...) -> SavingThrows (typed)
  - compute_skills(...) -> list[EntitySkill] (typed)
  - compute_armor_class, compute_initiative, compute_spell_numbers -> ints/tuple
  - Designed to work with EntityState + sheet.class_index.
  - Not wired yet (by design) until shapes are finalized.

### Data updates
- data/scenarios/goblin-cave-adventure/npcs/*.json
  - Converted NPC templates to `initial_*` fields; removed template-level `present`.

### Removed
- scripts/normalize_templates.py (migration already reflected in code + data; not needed).
- Character-only SSE events and commands.
- Deprecated runtime fields and logic from CharacterSheet and NPCSheet.

## Rationale / Key Design Choices
- Abilities are dynamic → live in EntityState (not template; modifiers are computed, not stored).
- Templates seed instances via explicit starting_* / initial_* fields; this avoids mixing runtime with definitions and improves clarity.
- ScenarioSheet embedded in ScenarioInstance makes saves portable and resilient to changes in source data.
- Use non-optional `current_location_id` with the sentinel value "unknown-location" for transitional/undefined scenes; avoids `None` handling while keeping type safety.
- Compute layer returns typed outputs (SavingThrows, EntitySkill) to improve type safety and avoid raw dicts.

## Remaining Work (detailed plan)
1) NPC movement tool (instead of auto-materialization)
   - All NPCs are instantiated at game start with `initial_location_id` and tracked via `NPCInstance.current_location_id`.
   - Add an explicit command/tool to move an existing NPCInstance between locations when needed (see TODO in LocationHandler).

2) Prefer embedded ScenarioSheet for static reads
   - In ContextService and similar read paths, use `game_state.scenario_instance.sheet` for static data (locations, encounters, quest defs) and `scenario_instance` for dynamic state (visited, danger, active_quests).
   - Keep ScenarioService for initial load and validation only.

3) Wire and extend compute layer (HIGH PRIORITY)
   - Use ICharacterComputeService to compute and set: ability modifiers, proficiency, saving throws, skills, AC, initiative, spell save DC/attack.
   - Extend the interface to cover base HP/Hit Dice and basic equipment-driven AC to remove placeholders in GameService.
   - Provide a `recompute_entity_state(sheet, state)` helper to refresh derived values after changes (level up, equipment changes), and call it in handlers as needed.

4) Initialization: switch to compute-driven values
   - Update `GameService._build_entity_state_from_sheet` to use the compute service for AC/initiative/saves/skills/HP/Hit Dice.
   - Ensure consistent initialization for both CharacterInstance and NPCInstance.

5) Fail-fast only (no legacy fallbacks)
   - Confirmed: SaveManager already raises if `instances/scenario.json` is missing; keep this behavior and remove any stale doc references to legacy fallback.

6) Frontend alignment with instance shape (MVP scope)
   - Fix saved games card to use `game.character.sheet.name`, `game.character.sheet.class_index`, `game.character.state.level`.
   - Remove unused `character_update` SSE listener; rely solely on `game_update`.
   - In `scenario_info` handler and other location reads, use `gameState.scenario_instance.current_location_id`.
   - Ensure inventory/currency read from `gameState.character.state.inventory` / `.currency` and conditions are plain strings.
   - Double-check location/quest/act panels use `scenario_instance` and embedded `sheet` correctly.

7) Optional follow-ups (post-MVP)
   - Add a minimal level-up flow using the compute service.
   - Consider on-demand compute (don’t persist derived fields) to avoid drift.

## Smoke Test Instructions
1) Create a new game via `/game/new`:
   - Expect `GameState.character.state` seeded from `starting_*` fields.
   - Expect `GameState.scenario_instance.sheet` populated; `current_location_id` set to starting location (or `"unknown-location"` for transitional scenes).
2) Mutate character state:
   - HP changes, inventory/currency modifications, short/long rest. Verify EntityState changes and saves under `instances/`.
3) Change location:
   - Confirm `scenario_instance.location_states` updates and `current_location_id` switches. NPC visibility in context/UI depends on `NPCInstance.current_location_id` matching the current location.
4) SSE events:
   - Confirm GAME_UPDATE events stream current GameState.

After these pass, we will implement NPC auto-materialization and begin migrating read paths to use embedded ScenarioSheet, followed by compute layer wiring.

## CLAUDE REVIEW (Critical Issues and Fixes)

### Issues Found

#### 1. **Compute Service Not Wired/Used**
**Issue**: `CharacterComputeService` exists but isn't used. All values are hardcoded defaults.
```python
# In GameService._build_entity_state_from_sheet:
armor_class=10,  # TODO: Wire compute layer
initiative=0,    # TODO: Wire compute layer
saving_throws=SavingThrows(),  # TODO: Wire compute layer
```
**Impact**: Characters have wrong stats (AC 10 for everyone, no proficiency applied, etc.)
**Fix Priority**: HIGH - game is unplayable with wrong stats.

#### 2. **Missing Instance ID Stability Validation**
**Issue**: Instance IDs use `uuid.uuid4()` on creation but no validation they remain stable across saves/loads.
**Risk**: If IDs regenerate, save/load round trips break references.
**Fix**: Add tests to verify ID persistence.
