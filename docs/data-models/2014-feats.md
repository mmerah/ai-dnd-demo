**SRD Feats (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Feats.json`
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

class FeatPrerequisitesItem(BaseModel):
    ability_score: ApiRef[Any]
    minimum_score: int

class Feat(BaseModel):
    desc: list[str]
    index: str
    name: str
    prerequisites: list['FeatPrerequisitesItem']
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Feat(BaseModel): index: str; name: str; description: str; prerequisites: str | None` (flatten SRD `desc[]`).
- Data: Create `data/feats.json` with these records.
- Repository: Add `FeatRepository` (required) for validations and UI.
 - Cross-references: If attached to classes/subclasses, store feat indexes in those catalogs.
 - Wiring: Update class/subclass catalogs to reference feats by index and validate.
