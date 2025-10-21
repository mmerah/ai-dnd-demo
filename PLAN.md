# Background System Enhancement Plan

## Executive Summary

Currently, the background system only stores a string index and provides no mechanical or narrative value. This plan implements a full D&D 5e background system that:
- Provides skill proficiencies, language choices, and starting equipment
- Offers background features (e.g., "Shelter of the Faithful")
- Supplies personality scaffolding (traits/ideals/bonds/flaws) for roleplay
- Integrates backgrounds into character creation and AI agent context
- Populates data with all 13 standard D&D 5e backgrounds

**Scope**: 13 tasks spanning models, services, data, migration scripts, and AI context

---

## Guiding Principles (from CLAUDE.md)

1. **SOLID first**: Narrow service responsibilities, interfaces before implementations
2. **Fail fast**: Validate backgrounds at startup, reject invalid data immediately
3. **Type safety**: Pydantic v2 everywhere, no `Any` types in background models
4. **DRY**: Reuse existing patterns (repository, compute service, context builders)
5. **No backwards compatibility**: Replace old minimal background model completely
6. **Tool-driven agents**: Business rules in services/tools, agents only orchestrate
7. **Content is data**: All 13 backgrounds in JSON, no hardcoded lore

---

## Current State Analysis

### What Exists ✅
- `BackgroundDefinition` model (minimal: index, name, description, content_pack)
- `BackgroundRepository` (full generic repository pattern)
- API endpoints (`/catalogs/backgrounds`, `/catalogs/backgrounds/{index}`)
- Validation at startup (CharacterService validates background indexes)
- CharacterSheet stores `background: str` (index reference)
- Content pack support

### What's Missing ❌
- Background proficiencies (skills, languages, tools)
- Background features (special abilities like "Shelter of the Faithful")
- Personality scaffolding (traits/ideals/bonds/flaws options)
- Starting equipment from backgrounds
- Application of background proficiencies to EntityState
- Background context in AI agents (agents have zero background knowledge)
- Data: Only 1 background (acolyte) exists, need 12 more

### Critical Gaps
1. **No mechanical effect**: Background provides no skills/proficiencies
2. **No roleplay support**: Agents don't know character backgrounds
3. **Incomplete data**: SRD has full structure, but migration script discards 90% of it
4. **Disconnected personality**: CharacterSheet.personality exists but has no link to background options

---

## Task Breakdown

### Phase 1: Data Model Enhancement

#### Task 1: Expand BackgroundDefinition Model
**Files**: `app/models/background.py`

**Rationale**: Current model only stores index/name/description. D&D 5e backgrounds provide mechanical benefits (proficiencies, equipment) and roleplay scaffolding (personality options). We need a model that captures this.

**Task**:
1. Read `docs/5e-database-snippets/src/2014/5e-SRD-Backgrounds.json` to understand full structure
2. Read `docs/data-models/2014-backgrounds.md` for intended migration strategy
3. Expand `BackgroundDefinition` to include:
   ```python
   class BackgroundOption(BaseModel):
       """A single personality option (trait/ideal/bond/flaw)."""
       text: str
       alignments: list[str] = Field(default_factory=list)  # For ideals only

   class BackgroundFeature(BaseModel):
       """Background-specific feature."""
       name: str
       description: str  # Multi-paragraph text

   class BackgroundDefinition(BaseModel):
       # Identity
       index: str
       name: str
       description: str  # Short summary

       # Feature
       feature: BackgroundFeature | None = None

       # Proficiencies
       skill_proficiencies: list[str] = Field(default_factory=list)  # e.g., ["insight", "religion"]
       tool_proficiencies: list[str] = Field(default_factory=list)  # e.g., ["smiths-tools"]
       language_count: int = 0  # Number of languages player can choose

       # Equipment (simplified - just store description for now)
       starting_equipment_description: str | None = None

       # Personality scaffolding
       personality_trait_options: list[str] = Field(default_factory=list)  # 8 options, choose 2
       ideal_options: list[BackgroundOption] = Field(default_factory=list)  # 6 options, choose 1
       bond_options: list[str] = Field(default_factory=list)  # 6 options, choose 1
       flaw_options: list[str] = Field(default_factory=list)  # 6 options, choose 1

       # Content pack metadata
       content_pack: str
   ```

**Expected Changes**:
- `app/models/background.py`: ~50 lines added
- Add imports for `Field` from pydantic
- Add nested `BackgroundOption` and `BackgroundFeature` classes
- All fields use proper Pydantic v2 syntax (Field, default_factory)

**Validation**:
- Run `mypy --strict app/models/background.py` to ensure type safety
- Ensure no `Any` types used

---

#### Task 2: Create Background-Specific Models (Optional Helper)
**Files**: None (inline with Task 1)

**Rationale**: BackgroundOption and BackgroundFeature could be separate models, but they're only used by BackgroundDefinition. Keep them inline to reduce complexity (KISS principle).

**Task**: Skip - already handled in Task 1 with inline models.

---

### Phase 2: Data Migration & Population

#### Task 3: Enhance Background Migration Script
**Files**: `scripts/migrate_backgrounds_from_srd.py`

**Rationale**: Current script only extracts index, name, and feature.desc. Need to extract full structure from SRD.

**Task**:
1. Read current script pattern from `scripts/migrate_alignments_from_srd.py` (reference implementation)
2. Update `convert_background()` to extract:
   - Feature: name + desc[] → multi-paragraph string
   - Proficiencies: starting_proficiencies → skill_proficiencies list
   - Languages: language_options.choose → language_count
   - Equipment: starting_equipment + starting_equipment_options → summary string
   - Personality traits: personality_traits.from.options → list of strings
   - Ideals: ideals.from.options → list of BackgroundOption (with alignments)
   - Bonds: bonds.from.options → list of strings
   - Flaws: flaws.from.options → list of strings
3. Helper functions:
   ```python
   def extract_feature(feature_dict: dict[str, Any]) -> dict[str, Any]:
       return {
           "name": feature_dict.get("name"),
           "description": "\n\n".join(feature_dict.get("desc", []))
       }

   def extract_skill_proficiencies(profs: list[dict[str, Any]]) -> list[str]:
       return [p["index"].replace("skill-", "") for p in profs if p["index"].startswith("skill-")]

   def extract_ideals(ideals_dict: dict[str, Any]) -> list[dict[str, Any]]:
       options = ideals_dict.get("from", {}).get("options", [])
       return [
           {
               "text": opt["desc"],
               "alignments": [a["index"] for a in opt.get("alignments", [])]
           }
           for opt in options if opt.get("option_type") == "ideal"
       ]

   def extract_string_options(choices_dict: dict[str, Any]) -> list[str]:
       options = choices_dict.get("from", {}).get("options", [])
       return [opt["string"] for opt in options if opt.get("option_type") == "string"]
   ```

**Expected Changes**:
- `scripts/migrate_backgrounds_from_srd.py`: Rewrite `convert_background()` function
- Add helper functions for extraction (4 new functions, ~40 lines)
- Main conversion function grows from ~10 lines to ~60 lines
- Output JSON will be much richer

**Validation**:
- Run script: `python scripts/migrate_backgrounds_from_srd.py`
- Verify `data/backgrounds.json` contains full acolyte data
- Manually inspect JSON to ensure all fields populated

---

#### Task 4: Add 12 More Standard Backgrounds
**Files**: `scripts/migrate_backgrounds_from_srd.py`, `data/backgrounds.json`

**Rationale**: SRD only includes acolyte. D&D 5e Player's Handbook has 13 standard backgrounds. Following the `migrate_alignments_from_srd.py` pattern, we extract what's in SRD then add the rest manually.

**Task**:
1. After extracting acolyte from SRD, manually add 12 more backgrounds:
   - **Criminal** (Stealth, Deception, thieves' tools, Criminal Contact feature)
   - **Charlatan** (Deception, Sleight of Hand, disguise/forgery kits, False Identity feature)
   - **Entertainer** (Acrobatics, Performance, musical instrument, By Popular Demand feature)
   - **Folk Hero** (Animal Handling, Survival, artisan's tools, Rustic Hospitality feature)
   - **Guild Artisan** (Insight, Persuasion, artisan's tools, Guild Membership feature)
   - **Hermit** (Medicine, Religion, herbalism kit, Discovery feature)
   - **Noble** (History, Persuasion, gaming set, Position of Privilege feature)
   - **Outlander** (Athletics, Survival, musical instrument, Wanderer feature)
   - **Sage** (Arcana, History, languages x2, Researcher feature)
   - **Sailor** (Athletics, Perception, navigator's tools, Ship's Passage feature)
   - **Soldier** (Athletics, Intimidation, gaming set, Military Rank feature)
   - **Urchin** (Sleight of Hand, Stealth, disguise/thieves' tools, City Secrets feature)

2. Reference D&D 5e SRD/Basic Rules for accurate feature descriptions
3. Use web search if needed to get exact feature text (public SRD content)
4. Structure each with:
   - 8 personality trait options (choose 2)
   - 6 ideal options (choose 1, with alignment tags)
   - 6 bond options (choose 1)
   - 6 flaw options (choose 1)

**Implementation Pattern**:
```python
def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "docs/5e-database-snippets/src/2014/5e-SRD-Backgrounds.json"
    dst = root / "data/backgrounds.json"

    # Extract SRD backgrounds
    raw: list[dict[str, Any]] = json.load(src.open())
    backgrounds = [convert_background(b) for b in raw if b.get("index") and b.get("name")]

    # Add additional D&D 5e backgrounds
    additional_backgrounds = [
        {
            "index": "criminal",
            "name": "Criminal",
            "description": "You are an experienced criminal with a history of breaking the law.",
            "feature": {
                "name": "Criminal Contact",
                "description": "You have a reliable and trustworthy contact who acts as your liaison..."
            },
            "skill_proficiencies": ["deception", "stealth"],
            "tool_proficiencies": ["thieves-tools"],
            "language_count": 0,
            "personality_trait_options": [...],  # 8 options
            "ideal_options": [...],  # 6 options with alignments
            "bond_options": [...],  # 6 options
            "flaw_options": [...],  # 6 options
        },
        # ... 11 more backgrounds
    ]

    backgrounds.extend(additional_backgrounds)
    add_pack_fields(backgrounds, "srd")
    # ... rest of script
```

**Expected Changes**:
- `scripts/migrate_backgrounds_from_srd.py`: Add ~500-800 lines of background data
- `data/backgrounds.json`: Grow from ~10 lines to ~2000-3000 lines
- All 13 backgrounds with full personality scaffolding

**Validation**:
- Run script, verify 13 backgrounds in output
- Spot-check 3 backgrounds for completeness
- Validate JSON syntax with `python -m json.tool data/backgrounds.json`

---

### Phase 3: Service Layer Integration

#### Task 5: Update BackgroundRepository for New Model
**Files**: `app/services/data/repositories/background_repository.py`

**Rationale**: Repository's `_parse_item()` needs to parse the expanded model. Pydantic will handle most validation automatically.

**Task**:
1. Update `_parse_item()` to parse new fields:
   ```python
   def _parse_item(self, data: dict) -> BackgroundDefinition:
       # Pydantic handles nested models automatically
       return BackgroundDefinition(**data)
   ```
2. Pydantic v2 will auto-validate nested `BackgroundFeature` and `BackgroundOption` models
3. No other changes needed (repository is generic)

**Expected Changes**:
- `app/services/data/repositories/background_repository.py`: Replace `_parse_item()` with single line
- Total: 1 line changed (from manual field extraction to `**data`)

**Validation**:
- Start app: `python -m app.main` or `uvicorn app.main:app --reload`
- Watch for startup errors in background loading
- Check logs for any Pydantic validation failures

---

#### Task 6: Create Background Application Logic in ComputeService
**Files**: `app/services/character/compute_service.py`

**Rationale**: Currently, `compute_skills()` only uses `CharacterSheet.starting_skill_indexes`. We need to merge background proficiencies into the skill list.

**Task**:
1. Add new method to `CharacterComputeService`:
   ```python
   def get_background_skill_proficiencies(
       self,
       game_state: GameState,
       background_index: str,
   ) -> list[str]:
       """Get skill proficiencies granted by a background.

       Returns:
           List of skill indexes (e.g., ["insight", "religion"])
       """
       try:
           background_repo = self.repository_provider.get_background_repository_for(game_state)
           background = background_repo.get(background_index)
           return background.skill_proficiencies
       except RepositoryNotFoundError:
           logger.warning(f"Background {background_index} not found, no proficiencies granted")
           return []
   ```

2. Update `compute_skills()` to merge background proficiencies:
   ```python
   def compute_skills(
       self,
       game_state: GameState,
       class_index: str,
       background_index: str,  # NEW PARAMETER
       selected_skills: list[str],
       modifiers: AbilityModifiers,
       proficiency_bonus: int,
   ) -> list[SkillValue]:
       # Get background proficiencies
       background_skills = self.get_background_skill_proficiencies(game_state, background_index)

       # Merge: background + selected skills (deduplicate)
       chosen = list(set(background_skills + selected_skills))

       # ... rest of function unchanged
   ```

3. Update `initialize_entity_state()` to pass background:
   ```python
   skills = self.compute_skills(
       game_state,
       character.class_index,
       character.background,  # NEW: pass background
       character.starting_skill_indexes,
       modifiers,
       proficiency_bonus,
   )
   ```

**Expected Changes**:
- `app/services/character/compute_service.py`:
  - New method `get_background_skill_proficiencies()` (~15 lines)
  - Update `compute_skills()` signature (+1 param)
  - Update `compute_skills()` logic (+3 lines for merging)
  - Update `initialize_entity_state()` call (+1 param)
- Total: ~20 lines added/modified

**Validation**:
- Unit test: Create character with background "acolyte", verify skills include "insight" and "religion"
- Integration test: Load game, check character.state.skills contains background proficiencies

---

#### Task 7: Update ICharacterComputeService Interface
**Files**: `app/interfaces/services/character.py`

**Rationale**: SOLID principle - interfaces before implementations. Update interface to match new compute_skills signature.

**Task**:
1. Read current interface definition
2. Update `compute_skills()` signature to match implementation:
   ```python
   @abstractmethod
   def compute_skills(
       self,
       game_state: GameState,
       class_index: str,
       background_index: str,  # NEW
       selected_skills: list[str],
       modifiers: AbilityModifiers,
       proficiency_bonus: int,
   ) -> list[SkillValue]:
       """Compute skill values with proficiency bonuses from class and background."""
       pass
   ```

**Expected Changes**:
- `app/interfaces/services/character.py`: Update method signature (+1 param, update docstring)
- Total: 2 lines changed

**Validation**:
- Run `mypy --strict app` to ensure interface/implementation match
- No runtime validation needed (static type checking)

---

### Phase 4: AI Context Integration

#### Task 8: Create BackgroundContextBuilder
**Files**: `app/services/ai/context_builders/background_context_builder.py` (new file)

**Rationale**: Agents currently have zero background knowledge. They need character background information for authentic roleplay. Following existing context builder pattern.

**Task**:
1. Create new context builder following pattern from `current_state_builder.py`:
   ```python
   from app.interfaces.services.ai import IContextBuilder
   from app.models.game_state import GameState
   from app.services.ai.context_service import BuildContext

   class BackgroundContextBuilder(IContextBuilder):
       """Builds background context for character roleplay."""

       def should_include(self, game_state: GameState, context: BuildContext) -> bool:
           """Include if character has a background with a feature."""
           char_sheet = game_state.character.sheet
           return bool(char_sheet.background)

       def build(self, game_state: GameState, context: BuildContext) -> str | None:
           char_sheet = game_state.character.sheet

           try:
               background_repo = context.repository_provider.get_background_repository_for(game_state)
               background = background_repo.get(char_sheet.background)
           except Exception:
               return None

           parts = [f"Background: {background.name}"]

           if background.feature:
               parts.append(f"- Feature: {background.feature.name}")
               parts.append(f"  {background.feature.description}")

           if char_sheet.personality.traits:
               parts.append(f"- Personality Traits: {', '.join(char_sheet.personality.traits)}")

           if char_sheet.personality.ideals:
               parts.append(f"- Ideals: {', '.join(char_sheet.personality.ideals)}")

           if char_sheet.personality.bonds:
               parts.append(f"- Bonds: {', '.join(char_sheet.personality.bonds)}")

           if char_sheet.personality.flaws:
               parts.append(f"- Flaws: {', '.join(char_sheet.personality.flaws)}")

           return "\n".join(parts)
   ```

2. This builder provides:
   - Background name and feature
   - Character's chosen personality traits/ideals/bonds/flaws
   - Helps agents roleplay authentically

**Expected Changes**:
- New file `app/services/ai/context_builders/background_context_builder.py` (~50 lines)
- Follows IContextBuilder interface pattern

**Validation**:
- Unit test: Build context for character with acolyte background
- Verify output includes "Background: Acolyte" and "Feature: Shelter of the Faithful"

---

#### Task 9: Register BackgroundContextBuilder in ContextService
**Files**: `app/services/ai/context_service.py`

**Rationale**: Context builders must be registered in the ContextService to be used by agents.

**Task**:
1. Read `app/services/ai/context_service.py` to find builder registration
2. Import and register `BackgroundContextBuilder`:
   ```python
   from app.services.ai.context_builders.background_context_builder import BackgroundContextBuilder

   def __init__(self, repository_provider: IRepositoryProvider):
       self.repository_provider = repository_provider
       self.builders: list[IContextBuilder] = [
           CurrentStateBuilder(),
           ScenarioBuilder(),
           LocationBuilder(),
           BackgroundContextBuilder(),  # NEW: Add here
           # ... other builders
       ]
   ```

3. Position: Add after `CurrentStateBuilder` so background appears early in context

**Expected Changes**:
- `app/services/ai/context_service.py`:
  - Import `BackgroundContextBuilder` (+1 line)
  - Add to builders list (+1 line)
- Total: 2 lines added

**Validation**:
- Start game, trigger AI response
- Check debug logs (if `DEBUG_AGENT_CONTEXT=true`) to see background in context
- Verify agents can reference background features in responses

---

### Phase 5: Character & NPC Updates

#### Task 10: Update Existing Character Files
**Files**:
- `data/characters/aldric-swiftarrow.json`
- `data/scenarios/goblin-cave-adventure/npcs/guard-elena.json`
- `data/scenarios/goblin-cave-adventure/npcs/barkeep-tom.json`

**Rationale**: Current characters may have personalities that don't match background options. Need to either update backgrounds or update personalities to align.

**Task**:
1. For each character, check if `background` field matches personality:

   **Aldric Swiftarrow** (ranger, background: "acolyte"):
   - Current traits: "I place no stock in wealthy folk..." (outlander trait, not acolyte)
   - **Decision**: Change background from "acolyte" to "outlander" (fits better)
   - Outlander proficiencies: Athletics, Survival (already has survival in starting_skill_indexes)

   **Guard Elena** (fighter, background: "acolyte"):
   - Personality: Brave, Direct, Loyal (doesn't match acolyte)
   - **Decision**: Change background to "soldier" (fits caravan guard)
   - Soldier proficiencies: Athletics, Intimidation (already has both!)

   **Barkeep Tom** (fighter, background: "acolyte"):
   - Personality: Friendly, Knowledgeable, Cautious
   - **Decision**: Change background to "guild-artisan" (innkeeper's guild)
   - Guild Artisan proficiencies: Insight, Persuasion (has insight, add persuasion)

2. Update JSON files:
   ```json
   // aldric-swiftarrow.json line 8
   "background": "outlander",  // was "acolyte"

   // guard-elena.json line 23
   "background": "soldier",  // was "acolyte"

   // barkeep-tom.json line 22
   "background": "guild-artisan",  // was "acolyte"
   ```

3. Update `starting_skill_indexes` if needed to remove background skills (they'll be auto-applied now):
   - Aldric: Keep as-is (survival from class choice + background, no conflict)
   - Elena: Already has athletics + intimidation, perfect
   - Tom: Add "persuasion" to starting_skill_indexes (line 62)

**Expected Changes**:
- 3 character JSON files modified
- Each changes `background` field value
- Tom's file adds "persuasion" to skills
- Total: 4 lines changed across 3 files

**Validation**:
- Run app startup validation (will validate new background indexes exist)
- Load each character in a game, verify skills include background proficiencies
- Verify no duplicate skills in EntityState.skills

---

#### Task 11: Verify Background Skill Deduplication
**Files**: `app/services/character/compute_service.py` (validation only)

**Rationale**: With background proficiencies auto-applied, ensure no duplicate skills appear in character state.

**Task**:
1. Verify `compute_skills()` deduplicates properly (already done in Task 6 with `set()`)
2. Add explicit logging for debugging:
   ```python
   logger.debug(f"Background skills: {background_skills}")
   logger.debug(f"Selected skills: {selected_skills}")
   logger.debug(f"Merged skills (deduplicated): {chosen}")
   ```

**Expected Changes**:
- `app/services/character/compute_service.py`: Add 3 debug log statements
- Total: 3 lines added

**Validation**:
- Load character, enable debug logging
- Verify logs show deduplication working
- Check character state has no duplicate skills

---

### Phase 6: API & Testing

#### Task 12: Update API Response Schemas (if needed)
**Files**: `app/api/schemas/catalog_schemas.py` (check if exists)

**Rationale**: API responses may need updating if frontend expects new background fields.

**Task**:
1. Check if dedicated response schemas exist for backgrounds
2. If API uses `BackgroundDefinition` directly (likely), no changes needed
3. If custom schemas exist, update them to match new model

**Investigation Needed**:
- Search for `BackgroundDefinition` in `app/api/routers/catalogs.py`
- Current code returns `BackgroundDefinition` directly (no custom schema)
- **Conclusion**: No changes needed, API auto-reflects new model fields

**Expected Changes**: None (API endpoints already return full BackgroundDefinition)

**Validation**:
- Test API: `GET /api/catalogs/backgrounds/acolyte`
- Verify response includes new fields (feature, skill_proficiencies, etc.)
- Check frontend can handle additional fields gracefully (backwards compatible)

---

#### Task 13: Write Comprehensive Tests
**Files**:
- `tests/unit/test_background_compute.py` (new)
- `tests/integration/test_background_integration.py` (new)

**Rationale**: Validate background proficiencies apply correctly and integrate with character system.

**Task**:
1. **Unit Tests** (`test_background_compute.py`):
   ```python
   def test_get_background_skill_proficiencies(compute_service, mock_game_state):
       """Test extraction of background proficiencies."""
       skills = compute_service.get_background_skill_proficiencies(
           mock_game_state,
           "acolyte"
       )
       assert "insight" in skills
       assert "religion" in skills

   def test_compute_skills_merges_background(compute_service, mock_game_state):
       """Test skills merge background + selected without duplicates."""
       skills = compute_service.compute_skills(
           game_state=mock_game_state,
           class_index="fighter",
           background_index="acolyte",
           selected_skills=["athletics", "insight"],  # insight also from background
           modifiers=AbilityModifiers(...),
           proficiency_bonus=2,
       )
       skill_indexes = [s.name for s in skills]
       assert "insight" in skill_indexes  # No duplicate
       assert "religion" in skill_indexes  # From background
       assert "athletics" in skill_indexes  # From selected
       assert skill_indexes.count("insight") == 1  # Deduplicated
   ```

2. **Integration Tests** (`test_background_integration.py`):
   ```python
   def test_character_initialization_applies_background_skills(game_factory):
       """Test character creation applies background proficiencies."""
       character = load_character("aldric-swiftarrow")  # outlander background
       game = game_factory.initialize_game(character, "goblin-cave-adventure")

       char_instance = game.character
       skill_indexes = [s.name for s in char_instance.state.skills]

       # Outlander grants Athletics + Survival
       assert "athletics" in skill_indexes or "survival" in skill_indexes

   def test_background_context_in_agent_prompt(game_state, context_service):
       """Test background appears in agent context."""
       context = context_service.build_context(game_state, BuildContext(...))

       assert "Background: Outlander" in context
       assert "Feature: Wanderer" in context
   ```

3. **Test Coverage Requirements**:
   - Background repository loading
   - Proficiency extraction
   - Skill deduplication
   - Character initialization
   - Context building
   - API endpoints (if not already covered)

**Expected Changes**:
- 2 new test files (~100 lines each)
- Total: ~200 lines of test code

**Validation**:
- Run: `pytest tests/unit/test_background_compute.py -v`
- Run: `pytest tests/integration/test_background_integration.py -v`
- Run full suite: `pytest` (ensure no regressions)
- Coverage: `coverage run -m pytest && coverage report` (aim for >90% on new code)

---

## Migration & Rollout Strategy

### Step 1: Data Preparation (Tasks 1-4)
1. Update model (Task 1)
2. Update migration script (Task 3)
3. Add 12 backgrounds (Task 4)
4. Run migration, validate JSON
5. Commit: `git commit -m "feat: Expand background data model with proficiencies and personality"`

### Step 2: Service Integration (Tasks 5-7)
1. Update repository parser (Task 5)
2. Update compute service (Task 6)
3. Update interface (Task 7)
4. Commit: `git commit -m "feat: Apply background skill proficiencies to characters"`

### Step 3: AI Context (Tasks 8-9)
1. Create context builder (Task 8)
2. Register builder (Task 9)
3. Test with DEBUG_AGENT_CONTEXT=true
4. Commit: `git commit -m "feat: Add background context to AI agents"`

### Step 4: Character Updates (Tasks 10-11)
1. Update 3 character files (Task 10)
2. Verify deduplication (Task 11)
3. Test character loading
4. Commit: `git commit -m "fix: Update character backgrounds to match personalities"`

### Step 5: Testing & Validation (Tasks 12-13)
1. API validation (Task 12)
2. Write tests (Task 13)
3. Run full test suite
4. Commit: `git commit -m "test: Add comprehensive background system tests"`

### Step 6: Documentation & Cleanup
1. Update CLAUDE.md (add background system to structure docs)
2. Update IDEAS.md (mark background enhancement as complete)
3. Run pre-commit hooks: `pre-commit run --all-files`
4. Final commit: `git commit -m "docs: Update docs for background system enhancement"`

---

## Validation Checklist

- [ ] `mypy --strict app` passes (no type errors)
- [ ] `ruff format .` and `ruff check --fix .` pass
- [ ] `pytest` runs without failures
- [ ] `coverage report` shows >90% coverage on new code
- [ ] App starts without errors: `uvicorn app.main:app --reload`
- [ ] All 13 backgrounds load successfully
- [ ] Character with acolyte background gains insight + religion skills
- [ ] Background context appears in agent prompts (verify with debug logs)
- [ ] API endpoint `/api/catalogs/backgrounds` returns all 13 backgrounds
- [ ] API endpoint `/api/catalogs/backgrounds/acolyte` returns full background with feature
- [ ] No duplicate skills in character state
- [ ] Pre-commit hooks pass

---

## Risk Assessment

### Low Risk ✅
- Model expansion (additive, no breaking changes to existing fields)
- Repository update (Pydantic handles validation)
- Context builder (isolated, doesn't affect game logic)

### Medium Risk ⚠️
- Compute service changes (affects all character initialization)
  - **Mitigation**: Extensive unit tests, validate with existing characters
- Character file updates (manual JSON edits)
  - **Mitigation**: Validate with app startup, test game loading

### High Risk ❌
- None identified (no database migrations, no breaking API changes)

---

## Success Criteria

1. ✅ All 13 standard D&D 5e backgrounds available in data/backgrounds.json
2. ✅ Background proficiencies automatically applied to characters
3. ✅ No duplicate skills in character state
4. ✅ Agents have background knowledge and can reference features
5. ✅ All existing characters/NPCs load without errors
6. ✅ API endpoints return full background data
7. ✅ Test coverage >90% on new code
8. ✅ Type safety maintained (mypy --strict passes)
9. ✅ Documentation updated
10. ✅ No regressions in existing functionality

---

## Timeline Estimate

- **Phase 1** (Data Model): 1-2 hours
- **Phase 2** (Data Migration): 3-4 hours (most time on manual background entry)
- **Phase 3** (Service Layer): 1-2 hours
- **Phase 4** (AI Context): 1 hour
- **Phase 5** (Character Updates): 1 hour
- **Phase 6** (Testing): 2-3 hours

**Total**: 9-13 hours of focused development + testing

---

## Post-Implementation Notes

### Future Enhancements (Out of Scope)
1. **Equipment Application**: Currently only stores description, could auto-apply starting equipment
2. **Language Selection**: Currently just stores count, could provide selection UI
3. **Tool Proficiencies**: Tracked but not applied to any mechanics yet
4. **Background Feature Triggers**: Could create events/tools that trigger background features (e.g., "Use Shelter of the Faithful" tool when in temple)
5. **Custom Backgrounds**: Allow user-created backgrounds in content packs

### Maintenance Notes
- When adding new backgrounds, follow the structure in `data/backgrounds.json`
- All backgrounds must have content_pack field (for filtering)
- Personality options are guidance, not enforced (players can write custom personalities)
- Background features are narrative, not mechanical (no game rule enforcement)

---

## Questions to Resolve Before Starting

1. ✅ **Confirmed**: Use simplified equipment description (not full equipment application) - keeps scope manageable
2. ✅ **Confirmed**: Personality options are suggestions, not enforced - characters can have custom personalities
3. ✅ **Confirmed**: Background features are narrative-only (no tool implementation needed yet)
4. ⚠️ **TBD**: Should we validate that character.personality selections come from background options? (Probably no - too restrictive)
5. ⚠️ **TBD**: Should tool proficiencies be applied to any checks? (Probably defer - no tool check system exists yet)

---

**Plan Status**: Ready for review and execution
**Last Updated**: 2025-10-21
**Author**: AI Assistant (Claude Code)
