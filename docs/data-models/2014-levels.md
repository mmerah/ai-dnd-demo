**SRD Levels (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Levels.json`
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

class LevelSpellcasting(BaseModel):
    cantrips_known: Optional[int] = None
    spell_slots_level_1: Optional[int] = None
    spell_slots_level_2: Optional[int] = None
    spell_slots_level_3: Optional[int] = None
    spell_slots_level_4: Optional[int] = None
    spell_slots_level_5: Optional[int] = None
    spell_slots_level_6: Optional[int] = None
    spell_slots_level_7: Optional[int] = None
    spell_slots_level_8: Optional[int] = None
    spell_slots_level_9: Optional[int] = None
    spells_known: Optional[int] = None

class LevelClassSpecific(BaseModel):
    action_surges: Optional[int] = None
    bardic_inspiration_die: Optional[int] = None
    brutal_critical_dice: Optional[int] = None
    channel_divinity_charges: Optional[int] = None
    destroy_undead_cr: Optional[float | int] = None
    extra_attacks: Optional[int] = None
    indomitable_uses: Optional[int] = None
    magical_secrets_max_5: Optional[int] = None
    magical_secrets_max_7: Optional[int] = None
    magical_secrets_max_9: Optional[int] = None
    rage_count: Optional[int] = None
    rage_damage_bonus: Optional[int] = None
    song_of_rest_die: Optional[int] = None
    wild_shape_fly: Optional[bool] = None
    wild_shape_max_cr: Optional[float | int] = None
    wild_shape_swim: Optional[bool] = None

class Level(BaseModel):
    ability_score_bonuses: int
    class: ApiRef[Any]
    class_specific: 'LevelClassSpecific'
    features: list[ApiRef[Any]]
    index: str
    level: int
    prof_bonus: int
    spellcasting: Optional['LevelSpellcasting'] = None
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Documentation/Catalog: Keep levels data for reference tables (XP thresholds, proficiency bonus, features) to power helper UIs later; no immediate runtime coupling.
