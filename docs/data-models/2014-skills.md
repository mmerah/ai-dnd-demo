**SRD Skills (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Skills.json`
- Sampled: 18 entries (not full file)
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

class Skill(BaseModel):
    ability_score: ApiRef[Any]
    desc: list[str]
    index: str
    name: str
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Model: Define `Skill(BaseModel): name: str; ability: str; description: str | None` (flatten SRD `desc[]`).
- Data: Create `data/skills.json` with these records.
- Repository: Add `SkillRepository` (optional); characters can continue storing skill modifiers as plain dict for now.
 - Cross-references: Use skill indexes as keys in `CharacterSheet.skills` for consistency.
 - Wiring: Migrate `CharacterSheet.skills` to use index keys; validate via `SkillRepository` when needed.
