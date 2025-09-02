**SRD Proficiencies (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Proficiencies.json`
- Sampled: 100 entries (not full file)
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

class Proficiencie(BaseModel):
    classes: list[ApiRef[Any]]
    index: str
    name: str
    races: list[ApiRef[Any]]
    reference: ApiRef[Any]
    type: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Proficiency(BaseModel): index: str; name: str; type: str; description: str | None` (flatten SRD `desc[]` if present).
- Data: Create `data/proficiencies.json` with these records.
- Repository: Add `ProficiencyRepository` (list/get/validate) for use in validations (classes, races) and UI.
 - Cross-references: Store proficiency indexes in classes/races where applicable.
 - Wiring: Update class/race catalogs to reference proficiencies by index and validate.
