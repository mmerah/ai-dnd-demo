**SRD Features (2014) — Data Model**

- Source: `docs/5e-database-snippets/src/2014/5e-SRD-Features.json`
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

class FeatureFeatureSpecific(BaseModel):
    expertise_options: Optional['FeatureFeatureSpecificExpertiseOptions'] = None
    subfeature_options: Optional['FeatureFeatureSpecificSubfeatureOptions'] = None

class FeatureFeatureSpecificExpertiseOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['FeatureFeatureSpecificExpertiseOptionsFrom'] = None
    type: Optional[str] = None

class FeatureFeatureSpecificSubfeatureOptions(BaseModel):
    choose: Optional[int] = None
    from: Optional['FeatureFeatureSpecificSubfeatureOptionsFrom'] = None
    type: Optional[str] = None

class FeatureFeatureSpecificExpertiseOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['FeatureFeatureSpecificExpertiseOptionsFromOptionsItem']] = None

class FeatureFeatureSpecificSubfeatureOptionsFrom(BaseModel):
    option_set_type: Optional[str] = None
    options: Optional[list['FeatureFeatureSpecificSubfeatureOptionsFromOptionsItem']] = None

class FeatureFeatureSpecificExpertiseOptionsFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class FeatureFeatureSpecificSubfeatureOptionsFromOptionsItem(BaseModel):
    item: Optional[ApiRef[Any]] = None
    option_type: Optional[str] = None

class Feature(BaseModel):
    class: ApiRef[Any]
    desc: list[str]
    feature_specific: Optional['FeatureFeatureSpecific'] = None
    index: str
    level: int
    name: str
    parent: Optional[ApiRef[Any]] = None
    prerequisites: list[Any]
    reference: Optional[str] = None
    subclass: Optional[ApiRef[Any]] = None
    url: str

```

Notes
- Inlined references use `ApiRef[Any]` for clarity and to avoid circular dependencies.
- Shapes are inferred from a sample and may omit rare variants.

**Migration Strategy**
- Index: Add `index: str` for stable keys.
- Model: Define `Feature(BaseModel): index: str; name: str; description: str` (flatten SRD `desc[]`).
- Data: Create `data/features.json` with these records.
- Repository: Add `FeatureRepository` (required) so classes/subclasses can attach features.
 - Cross-references: Store feature indexes in `classes.json` and `subclasses.json`.
 - Wiring: Update class/subclass catalogs to reference features by index and validate.
