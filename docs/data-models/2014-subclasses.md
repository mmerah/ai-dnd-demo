**SRD Subclasses (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Subclasses.json`
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

class SubclasseSpellsItem(BaseModel):
    prerequisites: list['SubclasseSpellsItemPrerequisitesItem']
    spell: ApiRef[Any]

class SubclasseSpellsItemPrerequisitesItem(BaseModel):
    index: str
    name: str
    type: str
    url: str

class Subclasse(BaseModel):
    class: ApiRef[Any]
    desc: list[str]
    index: str
    name: str
    spells: Optional[list['SubclasseSpellsItem']] = None
    subclass_flavor: str
    subclass_levels: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` (kebab-case) for stable references.
- Catalog: Create `data/subclasses.json` with `{ index, name, parent_class: str }`.
- Repository: Add `SubclassRepository` (list/get/validate), ensure `parent_class` exists in `ClassRepository`.
- Character: Add `subclass: str | None` validated via repository.
- Spells: Prefer `subclasses: list[str]` of subclass indexes; resolve names via repository.
- Cross-references: Store subclass indexes immediately in all dependent data (e.g., spells, characters).
- Wiring: Ensure `CharacterSheet.subclass` stores a subclass index and is validated.
