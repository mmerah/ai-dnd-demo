**SRD Equipment-Categories (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Equipment-Categories.json`
- Sampled: 39 entries (not full file)
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

class EquipmentCategorie(BaseModel):
    equipment: list[ApiRef[Any]]
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `EquipmentCategory(BaseModel): index: str; name: str`.
- Data: Create `data/equipment_categories.json` with `{ index, name }`.
 - Repository: Add `EquipmentCategoryRepository` for validation/UI; items should store `equipment_category` as the category index (resolve name via repository).
