**SRD Traits (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Traits.json`
- Sampled: 38 entries (not full file)
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

class TraitLanguageOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['TraitLanguageOptionsFrom'] = None
    type: Optional[str] = None

class TraitProficiencyChoices(BaseModel):
    choose: Optional[int] = None
    from: Optional['TraitProficiencyChoicesFrom'] = None
    type: Optional[str] = None

class TraitTraitSpecific(BaseModel):
    breath_weapon: Optional['TraitTraitSpecificBreathWeapon'] = None
    damage_type: Optional[ApiRef[Any]] = None
    spell_options: Optional['TraitTraitSpecificSpellOptions'] = None
    subtrait_options: Optional['TraitTraitSpecificSubtraitOptions'] = None

class TraitLanguageOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['TraitLanguageOptionsFromOptionsItem']] = None

class TraitProficiencyChoicesFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['TraitProficiencyChoicesFromOptionsItem']] = None

class TraitTraitSpecificBreathWeapon(BaseModel):
    area_of_effect: Optional['TraitTraitSpecificBreathWeaponAreaOfEffect'] = None
    damage: Optional[list['TraitTraitSpecificBreathWeaponDamageItem']] = None
    dc: Optional['TraitTraitSpecificBreathWeaponDc'] = None
    desc: Optional[str] = None
    name: Optional[str] = None
    usage: Optional['TraitTraitSpecificBreathWeaponUsage'] = None

class TraitTraitSpecificSpellOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['TraitTraitSpecificSpellOptionsFrom'] = None
    type: Optional[str] = None

class TraitTraitSpecificSubtraitOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['TraitTraitSpecificSubtraitOptionsFrom'] = None
    type: Optional[str] = None

class TraitLanguageOptionsFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class TraitProficiencyChoicesFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class TraitTraitSpecificBreathWeaponDc(BaseModel):
    dc_type: Optional[ApiRef[Any]] = None
    success_type: Optional[str] = None

class TraitTraitSpecificBreathWeaponUsage(BaseModel):
    times: Optional[int] = None
    type: Optional[str] = None

class TraitTraitSpecificSpellOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['TraitTraitSpecificSpellOptionsFromOptionsItem']] = None

class TraitTraitSpecificSubtraitOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['TraitTraitSpecificSubtraitOptionsFromOptionsItem']] = None

class TraitTraitSpecificBreathWeaponDamageItem(BaseModel):
    damage_at_character_level: Optional[dict[int, str]] = None
    damage_type: Optional[ApiRef[Any]] = None

class TraitTraitSpecificBreathWeaponAreaOfEffect(BaseModel):
    size: Optional[int] = None
    type: Optional[str] = None

class TraitTraitSpecificSpellOptionsFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class TraitTraitSpecificSubtraitOptionsFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class Trait(BaseModel):
    desc: list[str]
    index: str
    language_options: Optional['TraitLanguageOptions'] = None
    name: str
    parent: Optional[ApiRef[Any]] = None
    proficiencies: list[ApiRef[Any]]
    proficiency_choices: Optional['TraitProficiencyChoices'] = None
    races: list[ApiRef[Any]]
    subraces: list[ApiRef[Any]]
    trait_specific: Optional['TraitTraitSpecific'] = None
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Model: Define `Trait(BaseModel): name: str; description: str` (flatten SRD `desc[]`).
- Data: Create `data/traits.json` with `{ name, description }`.
- Repository: Add `TraitRepository` (read-only) for validation and UI.
 - Cross-references: Store trait indexes in `races.json` and `subraces.json`.
 - Wiring: Ensure character race/subrace derived traits can be resolved by index for UI.
