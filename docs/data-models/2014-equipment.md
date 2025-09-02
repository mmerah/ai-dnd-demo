**SRD Equipment (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Equipment.json`
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

class EquipmentCost(BaseModel):
    quantity: int
    unit: str

class EquipmentDamage(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class EquipmentRange(BaseModel):
    long: Optional[int] = None
    normal: Optional[int] = None

class EquipmentArmorClass(BaseModel):
    base: Optional[int] = None
    dex_bonus: Optional[bool] = None
    max_bonus: Optional[int] = None

class EquipmentThrowRange(BaseModel):
    long: Optional[int] = None
    normal: Optional[int] = None

class EquipmentTwoHandedDamage(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class Equipment(BaseModel):
    armor_category: Optional[str] = None
    armor_class: Optional['EquipmentArmorClass'] = None
    category_range: Optional[str] = None
    cost: 'EquipmentCost'
    damage: Optional['EquipmentDamage'] = None
    desc: Optional[list[str]] = None
    equipment_category: ApiRef[Any]
    gear_category: Optional[ApiRef[Any]] = None
    image: Optional[str] = None
    index: str
    name: str
    properties: Optional[list[ApiRef[Any]]] = None
    quantity: Optional[int] = None
    range: Optional['EquipmentRange'] = None
    special: Optional[list[str]] = None
    stealth_disadvantage: Optional[bool] = None
    str_minimum: Optional[int] = None
    throw_range: Optional['EquipmentThrowRange'] = None
    two_handed_damage: Optional['EquipmentTwoHandedDamage'] = None
    url: str
    weapon_category: Optional[str] = None
    weapon_range: Optional[str] = None
    weight: float | int

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` to `ItemDefinition` for stable references.
- Model: Extend `app/models/item.py` `ItemDefinition` with optional strings: `equipment_category`, `weapon_category`, `weapon_range`, `category_range`.
- Data: Replace `data/items.json` with SRD equipment mapped into `ItemDefinition`:
  - `name`, `description` (flatten SRD `desc[]` where available), `weight`, `value` (convert SRD cost to gp float), `damage`/`damage_type`, `properties` (names), subtype for weapons (`Melee`/`Ranged`).
  - Default `rarity` to `Common` for SRD equipment.
- Magic Items: Integrate SRD magic items into the same `ItemDefinition` where feasible (name, rarity, attunement as a boolean flag, description). Keep them in a separate file `data/magic_items.json` but managed by the same `ItemRepository`.
- Repository: Update `ItemRepository` to load from both `items.json` and `magic_items.json` and expose a unified API; key items by `index`.
 - Cross-references: Store category and property references as indexes (`equipment_category`, `properties[]` from `weapon_properties.json`), and damage type as an index.
 - Wiring: Update `ItemDefinition` fields accordingly and validate via repositories.
