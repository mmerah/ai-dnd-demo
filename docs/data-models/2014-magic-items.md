**SRD Magic-Items (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Magic-Items.json`
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

class MagicItem(BaseModel):
    desc: list[str]
    equipment_category: ApiRef[Any]
    image: Optional[str] = None
    index: str
    name: str
    rarity: ApiRef[Any]
    url: str
    variant: bool
    variants: list[ApiRef[Any]]

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` to `ItemDefinition` for stable keys.
- Model: Reuse `ItemDefinition` with `rarity` and an `attunement: bool | None` addition if needed.
- Data: Create `data/magic_items.json` with mapped SRD magic items: `index`, `name`, `description` (flattened), `rarity`, `attunement?`, and any simple stats.
- Repository: Update `ItemRepository` to load both `items.json` and `magic_items.json`, returning a unified set of `ItemDefinition` keyed by `index`.
 - Cross-references: Store property references as property indexes; damage type as an index if applicable.
 - Wiring: Validate via `WeaponPropertyRepository` and `DamageTypeRepository`.
