# Project Progress — MVP1

This document tracks what’s been completed and what remains from CLAUDE-REVIEW.md.

## Completed Work

- Entity Architecture: Monster Instance Pattern
  - Renamed Monster → MonsterSheet (template only).
    - `app/models/monster.py`
  - Added MonsterInstance with runtime `state: EntityState` and `current_location_id`.
    - `app/models/instances/monster_instance.py`
  - GameState stores monster instances and dedupes display names.
    - `app/models/game_state.py`
  - Save format migrated (breaking change): monsters now saved under `instances/monsters/{instance_id}.json`.
    - `app/services/game/save_manager.py`
  - Introduced MonsterFactory (SRP): builds MonsterInstance from MonsterSheet (DI-friendly).
    - Interface: `IMonsterFactory` in `app/interfaces/services.py`
    - Impl: `app/services/game/monster_factory.py`
    - Injection: `app/container.py`
  - Updated flows to use instances end-to-end:
    - Scenario init materializes notable monsters via factory.
      - `app/services/game/game_service.py`
    - Combat spawns create instances via factory and add to GameState.
      - `app/events/handlers/combat_handler.py`
- Tools support monsters (ID-based):
    - HP/conditions updates target entities by `entity_id` + `entity_type` (player, npc, monster).
      - `app/events/commands/character_commands.py`, `app/tools/character_tools.py`, `app/events/handlers/character_handler.py`
- API returns MonsterSheet objects.
    - `app/api/routes.py`

- Unified Entity Interface (Phase 1)
  - Defined `ICombatEntity` protocol and `EntityType` alias.
    - `app/models/entity.py` (EntityType is now an Enum)
  - Added `display_name`/`is_alive()` to instances for consistency.
    - `app/models/instances/character_instance.py`
    - `app/models/instances/npc_instance.py`
    - `app/models/instances/monster_instance.py`
  - Updated `CombatParticipant` to reference stable `entity_id`/`entity_type`; removed `conditions`.
    - `app/models/combat.py`
  - Updated combat handlers to populate IDs and avoid name-only resolution.
    - `app/events/handlers/combat_handler.py`
  - Removed condition duplication; handlers now update entity state only.
    - `app/events/handlers/character_handler.py`
  - Added GameState helpers for unified entity lookup.
    - `app/models/game_state.py`

- Combat Turn Management Tools
  - Added `NextTurnCommand`/`EndCombatCommand` and handlers.
    - Commands: `app/events/commands/combat_commands.py`
    - Handlers: `app/events/handlers/combat_handler.py`
    - Tool bindings: `app/tools/combat_tools.py`
    - Results: `app/models/tool_results.py`
  - Registered new tools in narrative agent.
    - `app/agents/narrative/agent.py`
  - Added add/remove participant tools and commands.
    - Commands: `app/events/commands/combat_commands.py`
    - Tools: `app/tools/combat_tools.py`
    - Handler: `app/events/handlers/combat_handler.py`

- Combat Service (SOLID/DRY)
  - Introduced `ICombatService` and `CombatService` for initiative rolling and participant adds.
    - Interface: `app/interfaces/services.py`
    - Impl: `app/services/game/combat_service.py`
    - DI: `app/container.py`
  - Updated `CombatHandler` to use the service and roll initiative from entity state instead of placeholders.
    - `app/events/handlers/combat_handler.py`
  - Final sweep: removed redundant initiative computations in encounter/spawn paths and cleaned duplicate logs.
    - `app/events/handlers/combat_handler.py`

- Context
  - Added "Monsters Present" block listing runtime monsters with IDs and combat stats.
  - Added "Monsters in Combat" block with IDs, initiative, status, HP/AC, and conditions.
    - `app/services/ai/context_service.py`

- ID-based Character Tools (Phase 2 migration)
  - Updated commands and tools to target entities by `entity_id` + `entity_type` instead of name strings.
    - Commands: `app/events/commands/character_commands.py`
    - Tools: `app/tools/character_tools.py`
    - Handler: `app/events/handlers/character_handler.py`

- DRY Cleanup
  - Removed duplicate `GameService.set_quest_flag`; use `GameState.set_quest_flag` directly.
    - `app/services/game/game_service.py`

- DRY Models and Normalization
  - Shared models consolidated as attributes:
    - `AttackAction` and `SkillValue` live in `app/models/attributes.py`.
      - Replaced prior duplication (`MonsterAttack`, `MonsterSkill`; runtime `EntityAttack`, `EntitySkill`).
      - MonsterSheet now uses `AttackAction` and `SkillValue`.
        - `app/models/monster.py`
      - EntityState uses `AttackAction`/`SkillValue`.
        - `app/models/instances/entity_state.py`
  - MonsterRepository normalizes skills via `SkillRepository` to `SkillValue.index`.
    - `app/services/data/repositories/monster_repository.py`
  - Name de-duplication utility for consistent display names.
    - `app/utils/names.py`

- Sentinel Location Handling (already present, kept)
  - `unknown-location` handled specially in location state access.
    - `app/models/instances/scenario_instance.py`
    - `app/models/game_state.py`

## Remaining Work (from CLAUDE-REVIEW.md)

- Unified Entity Interface
  - Use `ICombatEntity` in any future combat action helpers (if introduced)

- Combat System
  - Optional: Add a formatted turn-order display helper on `CombatState` (context already covers it).

- ContextService Simplification
  - Remove `IScenarioService` dependency; build context directly from `game_state.scenario_instance.sheet`.
  - Update `app/agents/factory.py` construction accordingly.

- TODO Cleanup (Important)
  - Repository reverse lookups: add inverse mapping (`get_name_from_index`) where helpful.
    - `app/services/character/compute_service.py` TODO reference
  - NPC movement tool/handler to move `NPCInstance` between locations.
    - `app/events/handlers/location_handler.py` TODO reference
  - SSE events audit: verify usefulness and trim if unused.
    - `app/models/sse_events.py`

- Scenario/Location Data and Validation
  - Clean up location JSON: remove unused `npc_ids` fields.
    - Example: `data/scenarios/goblin-cave-adventure/locations/tavern.json`
  - Add location change validation: ensure traversable connections exist before `change_location`.
  - NPC location queries in GameState (helpers to list/query NPCs per location).

- Nice-to-Have (Defer to MVP2 unless time allows)
  - Equipment slot system.
  - Narrative formatting simplification for initial narrative.
  - Random encounters loader/usage.

## Migration Notes
- Breaking: Save format switched to `instances/monsters/` (no legacy fallback). Old saves are incompatible.
- Breaking: API catalog endpoints for monsters now return MonsterSheet, not runtime instances.
- Data: Monster skills are normalized to `SkillValue.index`. Unknown skills in dataset are logged and skipped.

## Next Steps (Recommended Order)
1. ContextService Simplification
   - Remove `IScenarioService` dependency; refactor builder to read from embedded scenario where possible.
2. Location Data & Validation
   - Clean JSON (`npc_ids`), add traversal validation for `ChangeLocation`.
3. NPC Movement
   - Implement NPC movement tool/handler and event flow.
4. Repository Inverse Lookups
   - Add reverse mapping helpers (e.g., `get_name_from_index`) where referenced.
5. Combat Polish (Optional)
   - Add `CombatState.get_turn_order_display()` helper if needed; context already shows order with IDs/initiative.
6. SSE Audit and Narrative Polish
   - Trim unused events and improve initial narrative formatting.
