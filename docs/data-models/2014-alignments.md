**SRD Alignments (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Alignments.json`
- Sampled: 9 entries (not full file)
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

class Alignment(BaseModel):
    abbreviation: str
    desc: str
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Alignment(BaseModel): index: str; name: str; description: str` (flatten SRD `desc[]`).
- Data: Create `data/alignments.json` with `[{ index, name, description }]`.
- Repository: Add `AlignmentRepository` for validation and UI.
 - Wiring: Update `CharacterSheet.alignment` and `NPCSheet.alignment` to store the alignment index (validate via repository).
