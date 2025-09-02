**SRD Damage-Types (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Damage-Types.json`
- Sampled: 13 entries (not full file)
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

class DamageType(BaseModel):
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
- Model: Define `DamageType(BaseModel): index: str; name: str; description: str | None` (flatten SRD `desc[]` if present).
- Data: Create `data/damage_types.json` with these records.
 - Cross-references: Store damage-type indexes immediately in items and spells (e.g., `ItemDefinition.damage_type`, `Spell.damage.damage_type`).
 - Wiring: Update item/spell fields to accept and validate damage-type indexes.
- Repository: Add `DamageTypeRepository` (required) to aid validation and UI.
