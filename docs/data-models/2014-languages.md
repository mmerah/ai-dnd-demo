**SRD Languages (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Languages.json`
- Sampled: 16 entries (not full file)
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

class Language(BaseModel):
    desc: Optional[str] = None
    index: str
    name: str
    script: Optional[str] = None
    type: str
    typical_speakers: list[str]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Language(BaseModel): index: str; name: str; type: str | None; script: str | None; description: str | None` (flatten SRD `desc[]`).
- Data: Create `data/languages.json` with these records.
- Repository: Add `LanguageRepository` for lookups and validations (characters, races, monsters).
 - Cross-references: Store language indexes immediately in character/race/monster data; resolve names via repository for display.
 - Wiring: Change `CharacterSheet.languages` to hold language indexes; for `NPCSheet`, replace string `languages` with `list[str]` of language indexes.
