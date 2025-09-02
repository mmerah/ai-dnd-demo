**SRD Spells (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Spells.json`
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

class SpellDamage(BaseModel):
    damage_at_character_level: Optional[dict[int, str]] = None
    damage_at_slot_level: Optional[dict[int, str]] = None
    damage_type: Optional[ApiRef[Any]] = None

class SpellDc(BaseModel):
    dc_success: Optional[str] = None
    dc_type: Optional[ApiRef[Any]] = None
    desc: Optional[str] = None

class SpellAreaOfEffect(BaseModel):
    size: Optional[int] = None
    type: Optional[str] = None

class Spell(BaseModel):
    area_of_effect: Optional['SpellAreaOfEffect'] = None
    attack_type: Optional[str] = None
    casting_time: str
    classes: list[ApiRef[Any]]
    components: list[str]
    concentration: bool
    damage: Optional['SpellDamage'] = None
    dc: Optional['SpellDc'] = None
    desc: list[str]
    duration: str
    heal_at_slot_level: Optional[dict[int, str]] = None
    higher_level: Optional[list[str]] = None
    index: str
    level: int
    material: Optional[str] = None
    name: str
    range: str
    ritual: bool
    school: ApiRef[Any]
    subclasses: list[ApiRef[Any]]
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` (stable kebab-case slug; use SRD `index` when available) and prefer it as the repository key and for cross-references over time.
- Models: Update `app/models/spell.py` `SpellDefinition` to add fields aligned with SRD:
  - `classes: list[str]`, `subclasses: list[str]`
  - `components_list: list[str]` and `material: str | None` (remove legacy combined `components` string)
  - `area_of_effect: { size: int; type: str } | None`, `attack_type: str | None`
  - `dc: { dc_type: str; dc_success: str } | None`
  - `damage_at_slot_level: dict[int, str | int] | None`, `heal_at_slot_level: dict[int, str | int] | None`
  - Keep `ritual: bool`, `concentration: bool`, `higher_levels: str | None`, `description: str` (desc paragraphs joined)
- Data: Replace `data/spells.json` with SRD-mapped content (single source of truth):
  - Map SRD `desc[]` → `description` (paragraphs joined with blank lines); `higher_level[]` → `higher_levels` (joined)
  - Map `components[]` → `components_list`; `material` → `material`
  - Map `classes`/`subclasses` to lists of indexes (preferred) or names (temporary); repositories resolve to display names.
  - Map scaling to `damage_at_slot_level`/`heal_at_slot_level` with int keys
- Repository: Update `SpellRepository` to parse the new fields only (no backward compatibility), keep query API unchanged; key by `index`.
- Validation: Add lightweight catalogs + repos for lookups (names only for now): `data/classes.json`, `data/subclasses.json`, `MagicSchools`, `Languages` as needed; validate spell `classes/subclasses` against catalogs.
