"""Read-only data catalog endpoints grouped under /catalogs/*."""

from fastapi import APIRouter, HTTPException

from app.container import container
from app.models.alignment import Alignment
from app.models.background import BackgroundDefinition
from app.models.class_definitions import ClassDefinition, SubclassDefinition
from app.models.condition import Condition
from app.models.damage_type import DamageType
from app.models.feat import FeatDefinition as FeatDef
from app.models.feature import FeatureDefinition as FeatureDef
from app.models.item import ItemDefinition
from app.models.language import Language
from app.models.magic_school import MagicSchool
from app.models.monster import MonsterSheet
from app.models.race import RaceDefinition
from app.models.race import SubraceDefinition as RaceSubraceDefinition
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition as TraitDef
from app.models.weapon_property import WeaponProperty

router = APIRouter()


# Items
@router.get("/catalogs/items")
async def list_items(keys_only: bool = False) -> list[ItemDefinition] | list[str]:
    """List all items (full objects by default, or keys with ?keys_only=true)."""
    repo = container.item_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[ItemDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/items/{index}")
async def get_item(index: str) -> ItemDefinition:
    repo = container.item_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{index}' not found")
    return item


# Spells
@router.get("/catalogs/spells")
async def list_spells(keys_only: bool = False) -> list[SpellDefinition] | list[str]:
    """List all spells (full objects by default, or keys with ?keys_only=true)."""
    repo = container.spell_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[SpellDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/spells/{index}")
async def get_spell(index: str) -> SpellDefinition:
    repo = container.spell_repository
    spell = repo.get(index)
    if not spell:
        raise HTTPException(status_code=404, detail=f"Spell '{index}' not found")
    return spell


# Monsters
@router.get("/catalogs/monsters")
async def list_monsters(keys_only: bool = False) -> list[MonsterSheet] | list[str]:
    """List all monsters (full objects by default, or keys with ?keys_only=true)."""
    repo = container.monster_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[MonsterSheet] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/monsters/{index}")
async def get_monster(index: str) -> MonsterSheet:
    repo = container.monster_repository
    monster = repo.get(index)
    if not monster:
        raise HTTPException(status_code=404, detail=f"Monster '{index}' not found")
    return monster


# Magic Schools
@router.get("/catalogs/magic_schools")
async def list_magic_schools(keys_only: bool = False) -> list[MagicSchool] | list[str]:
    repo = container.magic_school_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[MagicSchool] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/magic_schools/{index}")
async def get_magic_school(index: str) -> MagicSchool:
    repo = container.magic_school_repository
    ms = repo.get(index)
    if not ms:
        raise HTTPException(status_code=404, detail=f"Magic school '{index}' not found")
    return ms


# Alignment
@router.get("/catalogs/alignments")
async def list_alignments(keys_only: bool = False) -> list[Alignment] | list[str]:
    repo = container.alignment_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Alignment] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/alignments/{index}")
async def get_alignment(index: str) -> Alignment:
    repo = container.alignment_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Alignment '{index}' not found")
    return item


# Classes
@router.get("/catalogs/classes")
async def list_classes(keys_only: bool = False) -> list[ClassDefinition] | list[str]:
    repo = container.class_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[ClassDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/classes/{index}")
async def get_class(index: str) -> ClassDefinition:
    repo = container.class_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Class '{index}' not found")
    return item


# Subclasses
@router.get("/catalogs/subclasses")
async def list_subclasses(keys_only: bool = False) -> list[SubclassDefinition] | list[str]:
    repo = container.subclass_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[SubclassDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/subclasses/{index}")
async def get_subclass(index: str) -> SubclassDefinition:
    repo = container.subclass_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Subclass '{index}' not found")
    return item


# Languages
@router.get("/catalogs/languages")
async def list_languages(keys_only: bool = False) -> list[Language] | list[str]:
    repo = container.language_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Language] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/languages/{index}")
async def get_language(index: str) -> Language:
    repo = container.language_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Language '{index}' not found")
    return item


# Conditions
@router.get("/catalogs/conditions")
async def list_conditions(keys_only: bool = False) -> list[Condition] | list[str]:
    repo = container.condition_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[Condition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/conditions/{index}")
async def get_condition(index: str) -> Condition:
    repo = container.condition_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Condition '{index}' not found")
    return item


# Races
@router.get("/catalogs/races")
async def list_races(keys_only: bool = False) -> list[RaceDefinition] | list[str]:
    repo = container.race_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[RaceDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/races/{index}")
async def get_race(index: str) -> RaceDefinition:
    repo = container.race_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Race '{index}' not found")
    return item


# Subraces
@router.get("/catalogs/race_subraces")
async def list_race_subraces(keys_only: bool = False) -> list[RaceSubraceDefinition] | list[str]:
    repo = container.race_subrace_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[RaceSubraceDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/race_subraces/{index}")
async def get_race_subrace(index: str) -> RaceSubraceDefinition:
    repo = container.race_subrace_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Race subrace '{index}' not found")
    return item


# Backgrounds
@router.get("/catalogs/backgrounds")
async def list_backgrounds(keys_only: bool = False) -> list[BackgroundDefinition] | list[str]:
    repo = container.background_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[BackgroundDefinition] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/backgrounds/{index}")
async def get_background(index: str) -> BackgroundDefinition:
    repo = container.background_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Background '{index}' not found")
    return item


# Traits
@router.get("/catalogs/traits")
async def list_traits(keys_only: bool = False) -> list[TraitDef] | list[str]:
    repo = container.trait_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[TraitDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/traits/{index}")
async def get_trait(index: str) -> TraitDef:
    repo = container.trait_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Trait '{index}' not found")
    return item


# Features
@router.get("/catalogs/features")
async def list_features(keys_only: bool = False) -> list[FeatureDef] | list[str]:
    repo = container.feature_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[FeatureDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/features/{index}")
async def get_feature(index: str) -> FeatureDef:
    repo = container.feature_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Feature '{index}' not found")
    return item


# Feats
@router.get("/catalogs/feats")
async def list_feats(keys_only: bool = False) -> list[FeatDef] | list[str]:
    repo = container.feat_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    out: list[FeatDef] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            out.append(item)
    return out


@router.get("/catalogs/feats/{index}")
async def get_feat(index: str) -> FeatDef:
    repo = container.feat_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Feat '{index}' not found")
    return item


# Skills
@router.get("/catalogs/skills")
async def list_skills(keys_only: bool = False) -> list[Skill] | list[str]:
    repo = container.skill_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[Skill] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/skills/{index}")
async def get_skill(index: str) -> Skill:
    repo = container.skill_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Skill '{index}' not found")
    return item


# Weapon Properties
@router.get("/catalogs/weapon_properties")
async def list_weapon_properties(keys_only: bool = False) -> list[WeaponProperty] | list[str]:
    repo = container.weapon_property_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[WeaponProperty] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/weapon_properties/{index}")
async def get_weapon_property(index: str) -> WeaponProperty:
    repo = container.weapon_property_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Weapon property '{index}' not found")
    return item


# Damage Types
@router.get("/catalogs/damage_types")
async def list_damage_types(keys_only: bool = False) -> list[DamageType] | list[str]:
    repo = container.damage_type_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[DamageType] = []
    for k in keys:
        item = repo.get(k)
        if item is not None:
            result.append(item)
    return result


@router.get("/catalogs/damage_types/{index}")
async def get_damage_type(index: str) -> DamageType:
    repo = container.damage_type_repository
    item = repo.get(index)
    if not item:
        raise HTTPException(status_code=404, detail=f"Damage type '{index}' not found")
    return item
