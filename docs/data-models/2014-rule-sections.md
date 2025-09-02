**SRD Rule-Sections (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Rule-Sections.json`
- Sampled: 33 entries (not full file)
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

class RuleSection(BaseModel):
    desc: str
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Documentation: Keep rule sections for indexing/navigation; no runtime coupling for now.
