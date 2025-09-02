**SRD Races (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Races.json`
- Sampled: 9 entries (not full file)
- Top-level: array of objects

**Pydantic Models**

```python
from __future__ import annotations
from typing import Any, Optional, Union, Generic, TypeVar, List, Dict
from pydantic import BaseModel
T = TypeVar('T')

class ApiRef(Generic[T], BaseModel):
    index: str
    name: str
    url: str

class RaceLanguageOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['RaceLanguageOptionsFrom'] = None
    type: Optional[str] = None

class RaceAbilityBonusOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['RaceAbilityBonusOptionsFrom'] = None
    type: Optional[str] = None

class RaceAbilityBonusesItem(BaseModel):
    ability_score: ApiRef[Any]
    bonus: int

class RaceLanguageOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['RaceLanguageOptionsFromOptionsItem']] = None

class RaceStartingProficiencyOptions(BaseModel):
    choose: Optional[int] = None
    desc: Optional[str] = None
    from: Optional['RaceStartingProficiencyOptionsFrom'] = None
    type: Optional[str] = None

class RaceAbilityBonusOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['RaceAbilityBonusOptionsFromOptionsItem']] = None

class RaceStartingProficiencyOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['RaceStartingProficiencyOptionsFromOptionsItem']] = None

class RaceLanguageOptionsFromOptionsItem(BaseModel):
    item: ApiRef[Any]
    option_type: str

class RaceAbilityBonusOptionsFromOptionsItem(BaseModel):
    ability_score: Optional[ApiRef[Any]] = None
    bonus: Optional[int] = None
    option_type: Optional[str] = None

class RaceStartingProficiencyOptionsFromOptionsItem(BaseModel):
    item: ApiRef[Any]
    option_type: str

class Race(BaseModel):
    ability_bonus_options: Optional['RaceAbilityBonusOptions'] = None
    ability_bonuses: list['RaceAbilityBonusesItem']
    age: str
    alignment: str
    index: str
    language_desc: str
    language_options: Optional['RaceLanguageOptions'] = None
    languages: list[ApiRef[Any]]
    name: str
    size: str
    size_description: str
    speed: int
    starting_proficiencies: list[ApiRef[Any]]
    starting_proficiency_options: Optional['RaceStartingProficiencyOptions'] = None
    subraces: list[ApiRef[Any]]
    traits: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` (kebab-case) for stable references.
- Model: Define `Race(BaseModel): index: str; name: str; speed: int; size: str; languages: list[str]; description: str | None; traits: list[str]` (flatten SRD descriptive fields as needed).
- Data: Create `data/races.json` with these records.
- Repository: Add `RaceRepository` for lookups and validation.
- Character: Keep `race: str`, add `subrace: str | None`.
- Optional: Create `data/subraces.json` and `SubraceRepository` (see Subraces migration) and validate `subrace` matches `race`.
 - Cross-references: Store race and subrace indexes immediately in character data; validate via repositories.
 - Wiring: Change `CharacterSheet.race` and `CharacterSheet.subrace` to index strings.
