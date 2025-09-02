**SRD Monsters (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Monsters.json`
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

class MonsterSenses(BaseModel):
    blindsight: Optional[str] = None
    darkvision: Optional[str] = None
    passive_perception: int
    tremorsense: Optional[str] = None
    truesight: Optional[str] = None

class MonsterSpeed(BaseModel):
    burrow: Optional[str] = None
    climb: Optional[str] = None
    fly: Optional[str] = None
    hover: Optional[bool] = None
    swim: Optional[str] = None
    walk: Optional[str] = None

class MonsterActionsItem(BaseModel):
    action_options: Optional['MonsterActionsItemActionOptions'] = None
    actions: Optional[list['MonsterActionsItemActionsItem']] = None
    attack_bonus: int
    attacks: Optional[list['MonsterActionsItemAttacksItem']] = None
    damage: list['MonsterActionsItemDamageItem']
    dc: Optional['MonsterActionsItemDc'] = None
    desc: str
    multiattack_type: Optional[str] = None
    name: str
    options: Optional['MonsterActionsItemOptions'] = None
    usage: Optional['MonsterActionsItemUsage'] = None

class MonsterProficienciesItem(BaseModel):
    proficiency: ApiRef[Any]
    value: int

class MonsterReactionsItem(BaseModel):
    dc: Optional['MonsterReactionsItemDc'] = None
    desc: Optional[str] = None
    name: Optional[str] = None

class MonsterActionsItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterActionsItemOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['MonsterActionsItemOptionsFrom'] = None
    type: Optional[str] = None

class MonsterActionsItemUsage(BaseModel):
    dice: Optional[str] = None
    min_value: Optional[int] = None
    rest_types: Optional[list[str]] = None
    times: Optional[int] = None
    type: Optional[str] = None

class MonsterArmorClassItem(BaseModel):
    armor: Optional[list[ApiRef[Any]]] = None
    condition: Optional[ApiRef[Any]] = None
    spell: Optional[ApiRef[Any]] = None
    type: str
    value: int

class MonsterLegendaryActionsItem(BaseModel):
    damage: Optional[list['MonsterLegendaryActionsItemDamageItem']] = None
    dc: Optional['MonsterLegendaryActionsItemDc'] = None
    desc: Optional[str] = None
    name: Optional[str] = None

class MonsterReactionsItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterSpecialAbilitiesItem(BaseModel):
    damage: Optional[list['MonsterSpecialAbilitiesItemDamageItem']] = None
    dc: Optional['MonsterSpecialAbilitiesItemDc'] = None
    desc: str
    name: str
    spellcasting: Optional['MonsterSpecialAbilitiesItemSpellcasting'] = None
    usage: Optional['MonsterSpecialAbilitiesItemUsage'] = None

class MonsterActionsItemActionOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['MonsterActionsItemActionOptionsFrom'] = None
    type: Optional[str] = None

class MonsterActionsItemActionsItem(BaseModel):
    action_name: Optional[str] = None
    count: Optional[int] = None
    type: Optional[str] = None

class MonsterActionsItemAttacksItem(BaseModel):
    damage: Optional[list['MonsterActionsItemAttacksItemDamageItem']] = None
    dc: Optional['MonsterActionsItemAttacksItemDc'] = None
    name: Optional[str] = None

class MonsterActionsItemDamageItem(BaseModel):
    choose: Optional[int] = None
    damage_dice: str
    damage_type: ApiRef[Any]
    dc: Optional['MonsterActionsItemDamageItemDc'] = None
    from: Optional['MonsterActionsItemDamageItemFrom'] = None
    type: Optional[str] = None

class MonsterActionsItemOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['MonsterActionsItemOptionsFromOptionsItem']] = None

class MonsterLegendaryActionsItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterSpecialAbilitiesItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterSpecialAbilitiesItemSpellcasting(BaseModel):
    ability: Optional[ApiRef[Any]] = None
    components_required: Optional[list[str]] = None
    dc: Optional[int] = None
    level: Optional[int] = None
    modifier: Optional[int] = None
    school: Optional[str] = None
    slots: Optional[dict[int, int]] = None
    spells: Optional[list['MonsterSpecialAbilitiesItemSpellcastingSpellsItem']] = None

class MonsterSpecialAbilitiesItemUsage(BaseModel):
    rest_types: Optional[list[str]] = None
    times: Optional[int] = None
    type: Optional[str] = None

class MonsterActionsItemActionOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['MonsterActionsItemActionOptionsFromOptionsItem']] = None

class MonsterActionsItemAttacksItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterActionsItemDamageItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterActionsItemDamageItemFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['MonsterActionsItemDamageItemFromOptionsItem']] = None

class MonsterLegendaryActionsItemDamageItem(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class MonsterSpecialAbilitiesItemDamageItem(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class MonsterActionsItemAttacksItemDamageItem(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class MonsterActionsItemOptionsFromOptionsItem(BaseModel):
    damage: Optional[list['MonsterActionsItemOptionsFromOptionsItemDamageItem']] = None
    dc: Optional['MonsterActionsItemOptionsFromOptionsItemDc'] = None
    name: Optional[str] = None
    option_type: Optional[str] = None

class MonsterSpecialAbilitiesItemSpellcastingSpellsItem(BaseModel):
    level: int
    name: str
    notes: Optional[str] = None
    url: str
    usage: Optional['MonsterSpecialAbilitiesItemSpellcastingSpellsItemUsage'] = None

class MonsterActionsItemActionOptionsFromOptionsItem(BaseModel):
    action_name: Optional[str] = None
    count: Optional[int] = None
    items: Optional[list['MonsterActionsItemActionOptionsFromOptionsItemItemsItem']] = None
    option_type: Optional[str] = None
    type: Optional[str] = None

class MonsterActionsItemDamageItemFromOptionsItem(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None
    notes: Optional[str] = None
    option_type: Optional[str] = None

class MonsterActionsItemOptionsFromOptionsItemDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    dc_value: Optional[int] = None
    success_type: Optional[str] = None

class MonsterSpecialAbilitiesItemSpellcastingSpellsItemUsage(BaseModel):
    times: Optional[int] = None
    type: Optional[str] = None

class MonsterActionsItemOptionsFromOptionsItemDamageItem(BaseModel):
    damage_dice: Optional[str] = None
    damage_type: Optional[ApiRef[Any]] = None

class MonsterActionsItemActionOptionsFromOptionsItemItemsItem(BaseModel):
    action_name: Optional[str] = None
    count: Optional[int] = None
    option_type: Optional[str] = None
    type: Optional[str] = None

class Monster(BaseModel):
    actions: list['MonsterActionsItem']
    alignment: str
    armor_class: list['MonsterArmorClassItem']
    challenge_rating: float | int
    charisma: int
    condition_immunities: list[ApiRef[Any]]
    constitution: int
    damage_immunities: list[Any | str]
    damage_resistances: list[Any | str]
    damage_vulnerabilities: list[Any | str]
    desc: Optional[str] = None
    dexterity: int
    hit_dice: str
    hit_points: int
    hit_points_roll: str
    image: str
    index: str
    intelligence: int
    languages: str
    legendary_actions: Optional[list['MonsterLegendaryActionsItem']] = None
    name: str
    proficiencies: list['MonsterProficienciesItem' | Any]
    proficiency_bonus: int
    reactions: Optional[list['MonsterReactionsItem']] = None
    senses: 'MonsterSenses'
    size: str
    special_abilities: Optional[list['MonsterSpecialAbilitiesItem']] = None
    speed: 'MonsterSpeed'
    strength: int
    subtype: Optional[str] = None
    type: str
    url: str
    wisdom: int
    xp: int

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` to `NPCSheet` for stable keys.
- Model: Extend `app/models/npc.py` `NPCSheet` with optional fields: `xp: int | None`, `proficiency_bonus: int | None`, `image: str | None`.
- Data: Replace `data/monsters.json` with SRD-mapped simplified blocks:
  - Flatten `speed` to string; choose a primary AC; map `actions` with `damage_dice`/type into `NPCAttack` items; special abilities into text.
- Repository: Update `MonsterRepository` to parse the new fields and coercions (keep HP normalization).
- Catalogs: Optionally add `data/conditions.json`, `data/languages.json` for validation if you plan to cross-reference by name.
