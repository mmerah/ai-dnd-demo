**SRD Conditions (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Conditions.json`
- Sampled: 15 entries (not full file)
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

class Condition(BaseModel):
    desc: list[str]
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Condition(BaseModel): index: str; name: str; description: str` (flatten SRD `desc[]`).
- Data: Create `data/conditions.json` with `{ index, name, description }`.
 - Cross-references: Store condition indexes immediately in `CharacterSheet.conditions` and any NPC status data.
 - Wiring: Ensure `CharacterSheet.conditions` holds condition indexes; validate via `ConditionRepository`.
- Repository: Add `ConditionRepository` (required) for validation and UI.
