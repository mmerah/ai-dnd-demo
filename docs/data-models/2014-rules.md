**SRD Rules (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Rules.json`
- Sampled: 6 entries (not full file)
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

class Rule(BaseModel):
    desc: str
    index: str
    name: str
    subsections: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Documentation: Keep SRD rules as static docs or markdown; no runtime coupling for now.
