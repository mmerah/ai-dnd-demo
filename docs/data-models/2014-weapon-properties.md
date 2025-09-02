**SRD Weapon-Properties (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Weapon-Properties.json`
- Sampled: 11 entries (not full file)
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

class WeaponPropertie(BaseModel):
    desc: list[str]
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Model: Define `WeaponProperty(BaseModel): name: str; description: str` (flatten SRD `desc[]`).
- Data: Create `data/weapon_properties.json` with `{ name, description }`.
- Repository: Add `WeaponPropertyRepository` (required) for UI; items store property names only.
