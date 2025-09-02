**SRD Magic-Schools (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Magic-Schools.json`
- Sampled: 8 entries (not full file)
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

class MagicSchool(BaseModel):
    desc: str
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Model: Define `MagicSchool(BaseModel): name: str; description: str | None` (flatten SRD `desc[]`).
- Data: Create `data/magic_schools.json` with these records.
- Repository: Add `MagicSchoolRepository` and use it as the source of truth for validation/UI. Keep `SpellSchool` enum aligned or derive it from the catalog.
 - Cross-references: Store the school index in spells; map to the enum for code usage if desired.
 - Wiring: Update `SpellDefinition.school` to use a school index or maintain an enum-to-index mapping; validate via repository.
