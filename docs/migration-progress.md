**SRD Migration — Progress and Handoff**

This document captures the current state of the SRD-aligned migration and outlines how to continue. It is written so anyone on the team can pick up and complete the migration without context loss.

**Scope**
- Goal: Migrate internal models, data, and repositories to SRD-compatible structures, using stable `index` strings and index-based cross-references across the board.
- Principle: Full migration (no backward-compat fields). Replace existing JSONs with SRD-mapped formats and update repos/models accordingly.

**Files to Review First**
- Code (models/repositories/services)
  - `app/models/spell.py` — updated to SRD-aligned fields.
  - `app/services/data/repositories/spell_repository.py` — parses new `data/spells.json` shape.
  - `app/container.py` — uses `SpellRepository` (no merged repo).
  - `app/api/routes.py` — `get_spell_details` still fetches by name; repo supports index or name.
  - `frontend/app.js` — spell tooltips currently expect `components` string and school as display name.
- Data + scripts
  - `data/spells.json` — regenerated, 319 spells, SRD-aligned (see Data format below).
  - `scripts/migrate_spells_from_srd.py` — one-shot migration of spells from SRD JSON.
  - `docs/data-models/*` — all schema docs include a “Migration Strategy” section with indexes + wiring notes.
- Reference (optional, some files are huge so only read 100 element per SRD-*.json)
  - `docs/5e-database-snippets/src/2014/5e-SRD-*.json` — SRD sources used for mapping.

**What’s Implemented**
- Spells
  - Model: `SpellDefinition` augmented to an SRD-aligned shape with new fields:
    - Identity: `index: str`, `name: str`
    - Core: `level: int`, `school: str` (school index), `casting_time`, `range`, `duration`, `description`, `higher_levels: str | None`
    - Components: `components_list: list[str]`, `material: str | None`
    - Flags: `ritual: bool`, `concentration: bool`
    - References: `classes: list[str]`, `subclasses: list[str]` (store indexes)
    - Mechanics: `area_of_effect`, `attack_type`, `dc`, `damage_at_slot_level`, `heal_at_slot_level`, `damage_at_character_level`
  - Repository: `SpellRepository` reads the new shape, caches keyed by `index`, supports lookups by index and name, and filters by school/class.
  - Data: `data/spells.json` is the single source of truth (no merge). Generated from SRD via `scripts/migrate_spells_from_srd.py`.
    - Desc arrays flattened to `description`/`higher_levels` strings
    - `components[]` → `components_list`, `material` preserved
    - `classes[]`/`subclasses[]` → index lists
    - `school` as school index (lowercase)
    - Scaling maps converted to `dict[int, str|int]`

**Immediate Impact/Notes**
- Backend API remains compatible for spell fetching by name (repo also supports index). Consider switching routes to index.
- Frontend tooltips reference `spellData.components` and `spellData.school` as display names; migration uses `components_list`/`material` and school index. The frontend needs a small adapter to render these fields.

**Data Format (Spells)**
- `data/spells.json` top-level: `{ "spells": SpellDefinition[] }`
- Each spell uses indexes for cross-references (classes, subclasses, school index string).

**How to Regenerate Spells from SRD**
- `python scripts/migrate_spells_from_srd.py`
  - Input: `docs/5e-database-snippets/src/2014/5e-SRD-Spells.json`
  - Output: `data/spells.json`

**Detailed TODO (Next Steps to Complete Migration)**

1) Classes & Subclasses (catalogs + validation)
- Add minimal catalogs (index-based) and repositories:
  - `data/classes.json` — entries: `{ index, name, hit_die, saving_throws: list[str], proficiencies: list[str], spellcasting_ability?: str, description?: str }`
  - `data/subclasses.json` — entries: `{ index, name, parent_class: str, description?: str, features?: list[str] }`
  - Repos: `ClassRepository`, `SubclassRepository` (list/get/validate by index)
- Wire spells validation against class/subclass repos if needed (optional for now).
- Update `CharacterSheet` (see step 2) to store class/subclass indexes.

2) CharacterSheet (index wiring)
- `app/models/character.py`
  - Add: `subclass: str | None`, `subrace: str | None` (store indexes)
  - Change: `class_name: str` → class index string (rename to `class_index: str` or keep name but change semantics)
  - Change: `alignment: str` → alignment index (see Alignments repo)
  - Change: `languages: list[str]` → list of language indexes
  - Change: `conditions: list[str]` → list of condition indexes
  - Optional: `skills: dict[str, int]` keys → skill indexes
- Update any validation logic and usage across services accordingly.

3) Alignments (catalog + wiring)
- Create `data/alignments.json` with `{ index, name, description }`
- Add `AlignmentRepository` (validate by index)
- Wire `CharacterSheet.alignment` and `NPCSheet.alignment` to store alignment index; validate via repo.

4) Races & Subraces (catalogs + validation)
- Create `data/races.json` with `{ index, name, speed, size, languages: list[str], description?: str, traits: list[str] }`
- Create `data/subraces.json` with `{ index, name, parent_race: str, description?: str, traits: list[str] }`
- Repos: `RaceRepository`, `SubraceRepository` (validate, enforce parent)
- Wire `CharacterSheet.race` and `CharacterSheet.subrace` to indexes (and adjust services/tests if any).

5) Languages (catalog + wiring)
- Create `data/languages.json` with `{ index, name, type?: str, script?: str, description?: str }`
- Add `LanguageRepository`
- Wire `CharacterSheet.languages: list[str]` (indexes) and migrate any NPC usage from plain string → list of language indexes.

6) Conditions (catalog + wiring)
- Create `data/conditions.json` with `{ index, name, description }`
- Add `ConditionRepository`
- Wire `CharacterSheet.conditions` to store condition indexes; validate via repo.

7) Skills (catalog + optional wiring)
- Create `data/skills.json` with `{ index, name, ability, description?: str }`
- Optional: Add `SkillRepository` and migrate `CharacterSheet.skills` dict keys to skill indexes.

8) Items & Magic Items (model extensions + data + repo)
- Extend `app/models/item.py` `ItemDefinition`:
  - Add: `index: str`
  - Add optional strings: `equipment_category`, `weapon_category`, `weapon_range`, `category_range`
  - Cross-references as indexes: `equipment_category`, `properties[]` (weapon property indexes), `damage_type` (damage type index)
- Data:
  - Replace `data/items.json` with SRD equipment mapped to `ItemDefinition` (flatten descriptions)
  - Add `data/magic_items.json` and map SRD magic items to the same `ItemDefinition` (use `rarity`, optional `attunement`)
- Repo:
  - Update `ItemRepository` to load both `items.json` and `magic_items.json`, unified set keyed by `index`
- Catalogs for validation/UI:
  - `data/equipment_categories.json` with `{ index, name }` + `EquipmentCategoryRepository`
  - `data/weapon_properties.json` with `{ index, name, description }` + `WeaponPropertyRepository`
  - `data/damage_types.json` with `{ index, name, description? }` + `DamageTypeRepository`

9) Monsters (model + data + wiring)
- Extend `app/models/npc.py` `NPCSheet`:
  - Add: `index: str`
  - Add optional: `xp: int | None`, `proficiency_bonus: int | None`, `image: str | None`
  - Change: `languages` string → `list[str]` of language indexes
- Data:
  - Convert SRD monsters to simplified `NPCSheet` shape: pick primary AC, flatten speed to string, map actions with `damage_dice`/type, special abilities as text
- Repo:
  - Update `MonsterRepository` parsing to accept new optional fields and normalized languages
- Validation: conditions/languages via their catalogs

10) Backgrounds / Features / Feats / Traits (catalogs + repos)
- Create catalogs with flattened descriptions and add repositories (required for validation/UI):
  - `data/backgrounds.json` → `BackgroundRepository` (wire `CharacterSheet.background` to index)
  - `data/features.json` → `FeatureRepository` (classes/subclasses can reference feature indexes)
  - `data/feats.json` → `FeatRepository` (optional references to classes/subclasses)
  - `data/traits.json` → `TraitRepository` (referenced by races/subraces)

11) Magic Schools (catalog)
- Create `data/magic_schools.json` with `{ index, name, description? }`
- Add `MagicSchoolRepository` and (optionally) map school index back to the existing `SpellSchool` enum for code using enums. Spells should keep `school` as the index.

12) Frontend adjustments (minimal)
- `frontend/app.js` spell tooltips:
  - Replace `spellData.components` with a small formatter that joins `components_list` and appends `(material)` when present
  - Convert `spellData.school` index to a display name (e.g., capitalize or use a lookup once `magic_schools.json` exists)

13) API routes (optional improvements)
- `/spells/{spell_name}` can be changed to `/spells/{spell_index}` or accept both; repository already supports both.

**Optional Testing/Validation Plan**
- Add smoke tests for repositories to ensure:
  - load all keys, get by index/name, validate references exist (e.g., spell classes/subclasses indexes exist in catalogs)
  - simple filters (by level, school, class) still work with the new data

**Notes & Decisions**
- All cross-references should store indexes immediately for consistency.
- Keep enums only where they add value; prefer catalogs + repos for validation/UI.
- Desc fields from SRD arrays are flattened to `description` strings for simplicity.

**Quick Commands**
- Regenerate spells: `python scripts/migrate_spells_from_srd.py`
- Validate repository behavior (interactive check):
  - Use a Python REPL to import `SpellRepository` and run `get("acid-arrow")`, `get_by_level(2)`, etc.

**Audit of Modified/Added Files**
- Modified
  - `app/models/spell.py` — SRD-aligned model fields
  - `app/services/data/repositories/spell_repository.py` — reads SRD-aligned data and keys by index
  - Many `docs/data-models/2014-*.md` — Migration Strategy sections with index + wiring notes
  - `app/container.py` — uses `SpellRepository`
- Added
  - `scripts/migrate_spells_from_srd.py` — converts SRD spells to internal JSON
  - `data/spells.json` — regenerated, SRD-aligned

**Contact / Handoff**
- The migration strategies in `docs/data-models/` are the source of truth for the remaining work. Proceed type-by-type, following the TODO above.

