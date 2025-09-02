**SRD Classes (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Classes.json`
- Sampled: 12 entries (not full file)
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

class ClasseSpellcasting(BaseModel):
    info: Optional[list['ClasseSpellcastingInfoItem']] = None
    level: Optional[int] = None
    spellcasting_ability: Optional[ApiRef[Any]] = None

class ClasseMultiClassing(BaseModel):
    prerequisite_options: Optional['ClasseMultiClassingPrerequisiteOptions'] = None
    prerequisites: Optional[list['ClasseMultiClassingPrerequisitesItem']] = None
    proficiencies: list[ApiRef[Any]]
    proficiency_choices: Optional[list['ClasseMultiClassingProficiencyChoicesItem']] = None

class ClasseProficiencyChoicesItem(BaseModel):
    choose: int
    desc: str
    from: 'ClasseProficiencyChoicesItemFrom'
    type: str

class ClasseSpellcastingInfoItem(BaseModel):
    desc: list[str]
    name: str

class ClasseStartingEquipmentItem(BaseModel):
    equipment: ApiRef[Any]
    quantity: int

class ClasseMultiClassingPrerequisiteOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['ClasseMultiClassingPrerequisiteOptionsFrom'] = None
    type: Optional[str] = None

class ClasseMultiClassingPrerequisitesItem(BaseModel):
    ability_score: ApiRef[Any]
    minimum_score: int

class ClasseProficiencyChoicesItemFrom(BaseModel):
    option_set_type: str
    options: list['ClasseProficiencyChoicesItemFromOptionsItem']

class ClasseStartingEquipmentOptionsItem(BaseModel):
    choose: int
    desc: str
    from: 'ClasseStartingEquipmentOptionsItemFrom'
    type: str

class ClasseMultiClassingPrerequisiteOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['ClasseMultiClassingPrerequisiteOptionsFromOptionsItem']] = None

class ClasseMultiClassingProficiencyChoicesItem(BaseModel):
    choose: Optional[int] = None
    desc: Optional[str] = None
    from: Optional['ClasseMultiClassingProficiencyChoicesItemFrom'] = None
    type: Optional[str] = None

class ClasseStartingEquipmentOptionsItemFrom(BaseModel):
    equipment_category: Optional[ApiRef[Any]] = None
    option_set_type: str
    options: list['ClasseStartingEquipmentOptionsItemFromOptionsItem']

class ClasseMultiClassingProficiencyChoicesItemFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['ClasseMultiClassingProficiencyChoicesItemFromOptionsItem']] = None

class ClasseProficiencyChoicesItemFromOptionsItem(BaseModel):
    choice: Optional['ClasseProficiencyChoicesItemFromOptionsItemChoice'] = None
    item: ApiRef[Any]
    option_type: str

class ClasseMultiClassingPrerequisiteOptionsFromOptionsItem(BaseModel):
    ability_score: Optional[ApiRef[Any]] = None
    minimum_score: Optional[int] = None
    option_type: Optional[str] = None

class ClasseProficiencyChoicesItemFromOptionsItemChoice(BaseModel):
    choose: Optional[int] = None
    desc: Optional[str] = None
    from: Optional['ClasseProficiencyChoicesItemFromOptionsItemChoiceFrom'] = None
    type: Optional[str] = None

class ClasseStartingEquipmentOptionsItemFromOptionsItem(BaseModel):
    choice: 'ClasseStartingEquipmentOptionsItemFromOptionsItemChoice'
    count: int
    items: Optional[list['ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItem']] = None
    of: ApiRef[Any]
    option_type: str
    prerequisites: Optional[list['ClasseStartingEquipmentOptionsItemFromOptionsItemPrerequisitesItem']] = None

class ClasseMultiClassingProficiencyChoicesItemFromOptionsItem(BaseModel):
    item: ApiRef[Any]
    option_type: str

class ClasseProficiencyChoicesItemFromOptionsItemChoiceFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['ClasseProficiencyChoicesItemFromOptionsItemChoiceFromOptionsItem']] = None

class ClasseStartingEquipmentOptionsItemFromOptionsItemChoice(BaseModel):
    choose: int
    desc: str
    from: 'ClasseStartingEquipmentOptionsItemFromOptionsItemChoiceFrom'
    type: str

class ClasseStartingEquipmentOptionsItemFromOptionsItemChoiceFrom(BaseModel):
    equipment_category: ApiRef[Any]
    option_set_type: str

class ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItem(BaseModel):
    choice: Optional['ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItemChoice'] = None
    count: int
    of: ApiRef[Any]
    option_type: str

class ClasseStartingEquipmentOptionsItemFromOptionsItemPrerequisitesItem(BaseModel):
    proficiency: Optional[ApiRef[Any]] = None
    type: Optional[str] = None

class ClasseProficiencyChoicesItemFromOptionsItemChoiceFromOptionsItem(BaseModel):
    item: ApiRef[Any]
    option_type: str

class ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItemChoice(BaseModel):
    choose: Optional[int] = None
    desc: Optional[str] = None
    from: Optional['ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItemChoiceFrom'] = None
    type: Optional[str] = None

class ClasseStartingEquipmentOptionsItemFromOptionsItemItemsItemChoiceFrom(BaseModel):
    equipment_category: Optional[ApiRef[Any]] = None
    option_set_type: Optional[str] = None

class Classe(BaseModel):
    class_levels: str
    hit_die: int
    index: str
    multi_classing: 'ClasseMultiClassing'
    name: str
    proficiencies: list[ApiRef[Any]]
    proficiency_choices: list['ClasseProficiencyChoicesItem']
    saving_throws: list[ApiRef[Any]]
    spellcasting: Optional['ClasseSpellcasting'] = None
    spells: Optional[str] = None
    starting_equipment: list['ClasseStartingEquipmentItem' | Any]
    starting_equipment_options: list['ClasseStartingEquipmentOptionsItem']
    subclasses: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` (kebab-case) for stable references.
- Model: Define `Classe(BaseModel)` for catalog entries with `{ index: str, name: str, hit_die: int, saving_throws: list[str], proficiencies: list[str], spellcasting_ability?: str, description?: str }` (flatten SRD `desc[]` if present).
- Data: Create `data/classes.json` containing these records.
- Repository: Add `ClassRepository` (list/get/validate by name) to back validations and lookups.
- Character: Keep `class_name: str`, add `subclass: str | None` (names validated via repos).
- Spells: Use `classes: list[str]` with values from this catalog.
 - Cross-references: Store class and subclass indexes immediately in all dependent data (e.g., spells, characters).
 - Wiring: Change `CharacterSheet.class_name` to the class index; ensure validations via `ClassRepository`.
