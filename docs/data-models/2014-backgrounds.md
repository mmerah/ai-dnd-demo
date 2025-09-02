**SRD Backgrounds (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Backgrounds.json`
- Sampled: 1 entries (not full file)
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

class BackgroundBonds(BaseModel):
    choose: int
    from: 'BackgroundBondsFrom'
    type: str

class BackgroundFeature(BaseModel):
    desc: list[str]
    name: str

class BackgroundFlaws(BaseModel):
    choose: int
    from: 'BackgroundFlawsFrom'
    type: str

class BackgroundIdeals(BaseModel):
    choose: int
    from: 'BackgroundIdealsFrom'
    type: str

class BackgroundBondsFrom(BaseModel):
    option_set_type: str
    options: list['BackgroundBondsFromOptionsItem']

class BackgroundFlawsFrom(BaseModel):
    option_set_type: str
    options: list['BackgroundFlawsFromOptionsItem']

class BackgroundIdealsFrom(BaseModel):
    option_set_type: str
    options: list['BackgroundIdealsFromOptionsItem']

class BackgroundLanguageOptions(BaseModel):
    choose: int
    from: 'BackgroundLanguageOptionsFrom'
    type: str

class BackgroundPersonalityTraits(BaseModel):
    choose: int
    from: 'BackgroundPersonalityTraitsFrom'
    type: str

class BackgroundLanguageOptionsFrom(BaseModel):
    option_set_type: str
    resource_list_url: str

class BackgroundPersonalityTraitsFrom(BaseModel):
    option_set_type: str
    options: list['BackgroundPersonalityTraitsFromOptionsItem']

class BackgroundStartingEquipmentItem(BaseModel):
    equipment: ApiRef[Any]
    quantity: int

class BackgroundBondsFromOptionsItem(BaseModel):
    option_type: str
    string: str

class BackgroundFlawsFromOptionsItem(BaseModel):
    option_type: str
    string: str

class BackgroundIdealsFromOptionsItem(BaseModel):
    alignments: list[ApiRef[Any]]
    desc: str
    option_type: str

class BackgroundStartingEquipmentOptionsItem(BaseModel):
    choose: int
    from: 'BackgroundStartingEquipmentOptionsItemFrom'
    type: str

class BackgroundPersonalityTraitsFromOptionsItem(BaseModel):
    option_type: str
    string: str

class BackgroundStartingEquipmentOptionsItemFrom(BaseModel):
    equipment_category: ApiRef[Any]
    option_set_type: str

class Background(BaseModel):
    bonds: 'BackgroundBonds'
    feature: 'BackgroundFeature'
    flaws: 'BackgroundFlaws'
    ideals: 'BackgroundIdeals'
    index: str
    language_options: 'BackgroundLanguageOptions'
    name: str
    personality_traits: 'BackgroundPersonalityTraits'
    starting_equipment: list['BackgroundStartingEquipmentItem']
    starting_equipment_options: list['BackgroundStartingEquipmentOptionsItem']
    starting_proficiencies: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Model: Define `Background(BaseModel): name: str; description: str; feature: str | None; proficiencies: list[str]; languages: list[str]` (flatten SRD `desc[]` → `description`).
- Data: Create `data/backgrounds.json` with flattened descriptions.
- Repository: Add `BackgroundRepository` (required) for validation and UI.
 - Wiring: Update `CharacterSheet.background` to store the background index (validate via repository).
