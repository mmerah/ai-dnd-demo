# Project Progress — MVP1

This document tracks what’s been completed and what remains from CLAUDE-REVIEW.md.

## Summary
- Completed Phase 1 of the entity architecture refactor for monsters, including a full save-format migration and DRY model cleanup.
- Monsters now use instances with unified runtime state, created via a factory and persisted under instances/.
- Tools can now target monsters for HP and conditions updates by name.
- Several review items remain for later phases (combat turn tools, ContextService simplification, ID-based combat, location validation, etc.).

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
  - Tools now support monsters:
    - HP updates support monsters by display name.
    - Conditions add/remove mirror to monster state to reduce drift with `CombatParticipant.conditions`.
      - `app/events/handlers/character_handler.py`
  - API returns MonsterSheet objects.
    - `app/api/routes.py`

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

- Combat System (Phase 2)
  - Turn management tools: `next_turn`, `end_combat`; route via event-bus.
    - Add commands and handlers; wire tools in `app/tools/combat_tools.py`.
  - Extend CombatState for formatted turn-order display.
  - Resolve conditions source of truth by removing duplication from `CombatParticipant` and reading from entity state only.
  - Move `CombatParticipant` to ID-based with unified entity interface (e.g., `ICombatEntity`) and drop name-based lookups.

- ContextService Simplification
  - Remove `IScenarioService` dependency; build context directly from `game_state.scenario_instance.sheet`.
  - Update `app/agents/factory.py` construction accordingly.

- TODO Cleanup (Critical/Important)
  - Remove duplicate `GameService.set_quest_flag` (GameState method already exists).
    - `app/services/game/game_service.py`
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
1. Combat Phase 2
   - Add `NextTurnCommand`/`EndCombatCommand`, tool handlers, and broadcast updates.
   - Add `CombatState.get_turn_order_display()` helper for richer context.
   - Define `ICombatEntity`, migrate `CombatParticipant` to IDs, remove condition duplication.
2. ContextService Simplification
   - Remove `IScenarioService` dependency; refactor builder to read from embedded scenario.
3. Core TODOs
   - Remove duplicate `set_quest_flag` in GameService.
   - Add repository inverse lookups where referenced.
   - Implement NPC movement tool/handler.
4. Location Data & Validation
   - Clean JSON (`npc_ids`), add traversal validation for `ChangeLocation`.
5. Polish (MVP2)
   - SSE audit, narrative formatting pass, equipment slots, random encounters.

## Files Touched (Key)
- Models
  - `app/models/monster.py`, `app/models/attributes.py`, `app/models/instances/monster_instance.py`, `app/models/instances/entity_state.py`
- Persistence
  - `app/services/game/save_manager.py`
- Services
  - `app/services/game/game_service.py`, `app/services/game/monster_factory.py`, `app/services/data/repositories/monster_repository.py`
- Handlers/Tools
  - `app/events/handlers/combat_handler.py`, `app/events/handlers/character_handler.py`, `app/tools/character_tools.py`
- API & DI
  - `app/api/routes.py`, `app/container.py`, `app/interfaces/services.py`
- Utilities
  - `app/utils/names.py`
