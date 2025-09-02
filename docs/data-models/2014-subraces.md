**SRD Subraces (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Subraces.json`
- Sampled: 4 entries (not full file)
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

class SubraceLanguageOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['SubraceLanguageOptionsFrom'] = None
    type: Optional[str] = None

class SubraceAbilityBonusesItem(BaseModel):
    ability_score: ApiRef[Any]
    bonus: int

class SubraceLanguageOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['SubraceLanguageOptionsFromOptionsItem']] = None

class SubraceLanguageOptionsFromOptionsItem(BaseModel):
    item: ApiRef[Any]
    option_type: str

class Subrace(BaseModel):
    ability_bonuses: list['SubraceAbilityBonusesItem']
    desc: str
    index: str
    language_options: Optional['SubraceLanguageOptions'] = None
    languages: list[Any]
    name: str
    race: ApiRef[Any]
    racial_traits: list[ApiRef[Any]]
    starting_proficiencies: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` (kebab-case) for stable references.
- Model: Define `Subrace(BaseModel): index: str; name: str; parent_race: str; description: str | None; traits: list[str]` (flatten SRD descriptive fields as needed).
- Data: Create `data/subraces.json` with these records.
- Repository: Add `SubraceRepository` (list/get/validate) and ensure `parent_race` exists in `RaceRepository`.
- Character: Add `subrace: str | None` validated here.
 - Cross-references: Store subrace indexes immediately in dependent data.
 - Wiring: Ensure `CharacterSheet.subrace` stores a subrace index and is validated.
