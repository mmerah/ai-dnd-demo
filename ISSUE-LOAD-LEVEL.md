# Load Level Architecture: Current Limitations and Full Integration Path

## Current Architecture (Index-Reference System)

The current system uses a **simplified index-reference architecture** where:
- Character data contains **pre-calculated** stats and abilities
- SRD catalog references (feature_indexes, trait_indexes, etc.) are primarily for **display purposes**
- The character model directly stores all computed values rather than deriving them

### How It Currently Works

```
Character JSON → Contains Pre-Calculated Stats
    ↓
class_index: "ranger" → Used for display name only
feature_indexes: ["favored-enemy-1-type"] → Used for feature description lookup
trait_indexes: ["darkvision"] → Used for trait description lookup
    ↓
Frontend loads catalogs → Resolves indexes to names/descriptions
    ↓
Display to user (read-only reference)
```

### Current Limitations

1. **Static Character Stats**
   - Proficiency bonus, saving throws, skills are hardcoded in character JSON
   - Class definition doesn't dynamically apply its rules to the character
   - Level progression requires manual updates to all derived stats

2. **Feature Application**
   - Features are descriptive only, not mechanically applied
   - Example: "Fighting Style: Archery" is stored as custom_features text, not applied as +2 to ranged attacks
   - No automatic feature unlocking at level-up

3. **Class Progression**
   - No automatic hit die assignment from class
   - No automatic proficiency application
   - No automatic spellcasting ability determination
   - Multiclassing would require manual calculation

4. **Race/Subrace Application**
   - Racial ability score improvements are pre-calculated
   - Racial traits are references, not active modifiers
   - Speed, darkvision, etc. are manually set

5. **Equipment Effects**
   - Armor doesn't automatically calculate AC
   - Weapons don't derive attack/damage from stats
   - Magic item bonuses would need manual application

## Full Integration Architecture

### Proposed Dynamic System

```
Character Core Data (Minimal)
    ↓
class_index: "ranger" → Loads ClassDefinition
    ├── Applies hit_die: d10
    ├── Applies saving_throws: ["STR", "DEX"]
    ├── Applies proficiencies
    └── Applies spellcasting_ability: "WIS"
    ↓
race_index: "elf" → Loads RaceDefinition
    ├── Applies ability_score_improvements
    ├── Applies speed: 30
    └── Applies traits (darkvision, keen senses)
    ↓
level: 3 → Determines Features
    ├── Loads level-appropriate features
    ├── Calculates proficiency_bonus
    └── Unlocks spell slots
    ↓
Computed Character Sheet (Runtime)
```

### Implementation Requirements

#### 1. Character Model Refactor
```python
class Character(BaseModel):
    # Core Identity (stored)
    id: str
    name: str
    race_index: str
    subrace_index: str | None
    class_index: str
    subclass_index: str | None
    level: int
    background_index: str
    alignment_index: str
    
    # Base Abilities (stored)
    base_abilities: dict[str, int]  # Before racial modifiers
    
    # Choices Made (stored)
    custom_features: list[Feature]  # Player-specific choices
    selected_skills: list[str]
    selected_languages: list[str]
    
    # Everything else is COMPUTED at runtime
```

#### 2. Character Service Enhancement
```python
class CharacterService:
    def compute_character_sheet(self, character: Character) -> CharacterSheet:
        # Load definitions
        class_def = self.class_repo.get(character.class_index)
        race_def = self.race_repo.get(character.race_index)
        
        # Apply racial modifiers
        abilities = self._apply_racial_modifiers(
            character.base_abilities, 
            race_def
        )
        
        # Calculate derived stats
        ability_modifiers = self._calculate_modifiers(abilities)
        proficiency_bonus = self._get_proficiency_bonus(character.level)
        
        # Apply class features
        hit_die = class_def.hit_die
        saving_throws = self._calculate_saving_throws(
            class_def.saving_throws,
            ability_modifiers,
            proficiency_bonus
        )
        
        # Determine available features by level
        features = self._get_features_for_level(
            class_def.index,
            character.level
        )
        
        # Apply equipment effects
        ac = self._calculate_ac(character.inventory, abilities)
        
        return CharacterSheet(
            # ... all computed values
        )
```

#### 3. Level Progression System
```python
class LevelProgressionService:
    def level_up(self, character: Character) -> LevelUpResult:
        character.level += 1
        
        # Determine new features
        new_features = self._get_new_features(
            character.class_index,
            character.level
        )
        
        # Handle choices (e.g., Ability Score Improvement)
        choices_required = self._get_required_choices(new_features)
        
        # Roll hit die for HP increase
        hp_increase = self._roll_hit_die(character.class_index)
        
        return LevelUpResult(
            new_features=new_features,
            choices_required=choices_required,
            hp_increase=hp_increase
        )
```

#### 4. Feature Application Engine
```python
class FeatureEngine:
    def apply_feature(self, 
                     character: CharacterSheet, 
                     feature: FeatureDefinition) -> CharacterSheet:
        # Parse feature effects
        for effect in feature.effects:
            if effect.type == "bonus_to_attack":
                character.attack_bonus += effect.value
            elif effect.type == "resistance":
                character.resistances.append(effect.damage_type)
            elif effect.type == "skill_expertise":
                character.expertise.append(effect.skill)
        
        return character
```

### Migration Path

#### Phase 1: Dual System (Current State)
- Keep pre-calculated values in character JSON
- Use indexes for display only
- No breaking changes

#### Phase 2: Computed Properties
- Add computation layer that can derive stats
- Fall back to stored values if computation fails
- Validate computed vs stored values

#### Phase 3: Gradual Migration
- Start computing simple values (proficiency bonus)
- Move to ability modifiers, saving throws
- Finally compute complex interactions (features, equipment)

#### Phase 4: Full Dynamic System
- Character JSON only stores choices and base values
- Everything else computed at runtime
- Full support for:
  - Dynamic level progression
  - Multiclassing
  - Temporary effects
  - Magic item bonuses
  - Condition applications

### Benefits of Full Integration

1. **Accurate Rules Implementation**
   - Automatic application of D&D 5e rules
   - No manual calculation errors
   - Consistent with official rules

2. **Dynamic Gameplay**
   - Level-ups automatically grant features
   - Equipment changes immediately reflected
   - Conditions properly affect stats

3. **Extensibility**
   - Easy to add new classes/races/features
   - Homebrew content support
   - Custom rule variants

4. **Reduced Data Redundancy**
   - No duplicate information
   - Single source of truth for rules
   - Smaller save files

### Example: Ranger Level 3 Computation

#### Current (Pre-calculated)
```json
{
  "class_index": "ranger",
  "level": 3,
  "proficiency_bonus": 2,  // Hardcoded
  "saving_throws": {"STR": 3, "DEX": 5},  // Hardcoded
  "features_and_traits": [  // Manually listed
    {"name": "Favored Enemy", "description": "..."},
    {"name": "Natural Explorer", "description": "..."}
  ]
}
```

#### Full Integration (Computed)
```python
# Only store:
character = {
    "class_index": "ranger",
    "level": 3,
    "base_abilities": {"STR": 13, "DEX": 16, ...},
    "custom_features": [
        {"name": "Favored Enemy: Goblinoids", ...}  # Player choice
    ]
}

# Compute at runtime:
proficiency_bonus = 2  # From level 3
saving_throws = {
    "STR": 3,  # 13 STR (+1) + proficiency (2)
    "DEX": 5   # 16 DEX (+3) + proficiency (2)
}
features = [
    # Automatically determined from ranger class at level 3
    "favored-enemy-1-type",
    "natural-explorer-1-terrain-type",
    "fighting-style",
    "spellcasting-ranger",
    "ranger-archetype",
    "primeval-awareness"
]
```

### Challenges to Address

1. **Performance**
   - Computation overhead on each character load
   - Caching strategies needed
   - Potential for computation loops

2. **Data Migration**
   - Converting existing characters
   - Backward compatibility during transition
   - Validation of computed vs stored values

3. **Rule Complexity**
   - Stacking rules (advantage/disadvantage)
   - Conditional bonuses
   - Edge cases and exceptions

4. **UI Updates**
   - Real-time stat recalculation
   - Clear indication of bonus sources
   - Tooltip system for rule explanations

## Recommendation

For the MVP, the current simplified system is appropriate because:
- It works for the demo scenario
- Reduces complexity and development time
- Allows focus on core AI DM functionality

For a production system, implementing the full integration would provide:
- True D&D 5e rules compliance
- Support for full campaigns with level progression
- Flexibility for different character builds and playstyles

The migration can be done incrementally, starting with the most valuable features (level progression, multiclassing) and expanding over time.