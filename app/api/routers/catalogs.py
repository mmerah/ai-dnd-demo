"""Read-only data catalog endpoints grouped under /catalogs/*."""

import contextlib

from fastapi import APIRouter, HTTPException

from app.common.exceptions import RepositoryNotFoundError
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
from app.models.requests import ResolveNamesRequest, ResolveNamesResponse
from app.models.skill import Skill
from app.models.spell import SpellDefinition
from app.models.trait import TraitDefinition as TraitDef
from app.models.weapon_property import WeaponProperty

router = APIRouter()


# Name resolution endpoint
@router.post("/catalogs/resolve-names", response_model=ResolveNamesResponse)
async def resolve_names(request: ResolveNamesRequest) -> ResolveNamesResponse:
    """Resolve display names for any catalog items from their indexes.

    This endpoint provides a unified way to get human-readable names
    for any type of game entity given their indexes, using the game's
    content pack scope.
    """
    response = ResolveNamesResponse()

    # Get the game state and game-scoped repositories
    game_service = container.game_service
    repository_factory = container.repository_factory
    try:
        game_state = game_service.get_game(request.game_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Game '{request.game_id}' not found") from exc

    if request.items:
        item_repo = repository_factory.get_item_repository_for(game_state)
        for index in request.items:
            with contextlib.suppress(Exception):
                response.items[index] = item_repo.get_name(index)

    if request.spells:
        spell_repo = repository_factory.get_spell_repository_for(game_state)
        for index in request.spells:
            with contextlib.suppress(Exception):
                response.spells[index] = spell_repo.get_name(index)

    if request.monsters:
        monster_repo = repository_factory.get_monster_repository_for(game_state)
        for index in request.monsters:
            with contextlib.suppress(Exception):
                response.monsters[index] = monster_repo.get_name(index)

    if request.classes:
        class_repo = repository_factory.get_class_repository_for(game_state)
        for index in request.classes:
            with contextlib.suppress(Exception):
                response.classes[index] = class_repo.get_name(index)

    if request.races:
        race_repo = repository_factory.get_race_repository_for(game_state)
        for index in request.races:
            with contextlib.suppress(Exception):
                response.races[index] = race_repo.get_name(index)

    if request.alignments:
        alignment_repo = repository_factory.get_alignment_repository_for(game_state)
        for index in request.alignments:
            with contextlib.suppress(Exception):
                response.alignments[index] = alignment_repo.get_name(index)

    if request.backgrounds:
        background_repo = repository_factory.get_background_repository_for(game_state)
        for index in request.backgrounds:
            with contextlib.suppress(Exception):
                response.backgrounds[index] = background_repo.get_name(index)

    if request.feats:
        feat_repo = repository_factory.get_feat_repository_for(game_state)
        for index in request.feats:
            with contextlib.suppress(Exception):
                response.feats[index] = feat_repo.get_name(index)

    if request.features:
        feature_repo = repository_factory.get_feature_repository_for(game_state)
        for index in request.features:
            with contextlib.suppress(Exception):
                response.features[index] = feature_repo.get_name(index)

    if request.traits:
        trait_repo = repository_factory.get_trait_repository_for(game_state)
        for index in request.traits:
            with contextlib.suppress(Exception):
                response.traits[index] = trait_repo.get_name(index)

    if request.skills:
        skill_repo = repository_factory.get_skill_repository_for(game_state)
        for index in request.skills:
            with contextlib.suppress(Exception):
                response.skills[index] = skill_repo.get_name(index)

    if request.conditions:
        condition_repo = repository_factory.get_condition_repository_for(game_state)
        for index in request.conditions:
            with contextlib.suppress(Exception):
                response.conditions[index] = condition_repo.get_name(index)

    if request.languages:
        language_repo = repository_factory.get_language_repository_for(game_state)
        for index in request.languages:
            with contextlib.suppress(Exception):
                response.languages[index] = language_repo.get_name(index)

    if request.damage_types:
        damage_type_repo = repository_factory.get_damage_type_repository_for(game_state)
        for index in request.damage_types:
            with contextlib.suppress(Exception):
                response.damage_types[index] = damage_type_repo.get_name(index)

    if request.magic_schools:
        magic_school_repo = repository_factory.get_magic_school_repository_for(game_state)
        for index in request.magic_schools:
            with contextlib.suppress(Exception):
                response.magic_schools[index] = magic_school_repo.get_name(index)

    if request.subclasses:
        subclass_repo = repository_factory.get_subclass_repository_for(game_state)
        for index in request.subclasses:
            with contextlib.suppress(Exception):
                response.subclasses[index] = subclass_repo.get_name(index)

    if request.subraces:
        race_subrace_repo = repository_factory.get_race_subrace_repository_for(game_state)
        for index in request.subraces:
            with contextlib.suppress(Exception):
                response.subraces[index] = race_subrace_repo.get_name(index)

    if request.weapon_properties:
        weapon_property_repo = repository_factory.get_weapon_property_repository_for(game_state)
        for index in request.weapon_properties:
            with contextlib.suppress(Exception):
                response.weapon_properties[index] = weapon_property_repo.get_name(index)

    return response


# Items
@router.get("/catalogs/items")
async def list_items(keys_only: bool = False, packs: str | None = None) -> list[ItemDefinition] | list[str]:
    """List all items (full objects by default, or keys with ?keys_only=true).

    Args:
        keys_only: Return only keys instead of full objects
        packs: Comma-separated list of content pack IDs to filter by (e.g., "srd,custom1")
    """
    repo = container.item_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[ItemDefinition] = []
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    for k in keys:
        item = repo.get(k)
        pack = repo.get_item_pack_id(k) or "srd"
        if selected_packs is None or pack in selected_packs:
            result.append(item)
    return result


@router.get("/catalogs/items/{index}")
async def get_item(index: str) -> ItemDefinition:
    repo = container.item_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Item '{index}' not found") from e


# Spells
@router.get("/catalogs/spells")
async def list_spells(keys_only: bool = False, packs: str | None = None) -> list[SpellDefinition] | list[str]:
    """List all spells (full objects by default, or keys with ?keys_only=true).

    Args:
        keys_only: Return only keys instead of full objects
        packs: Comma-separated list of content pack IDs to filter by (e.g., "srd,custom1")
    """
    repo = container.spell_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[SpellDefinition] = []
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    for k in keys:
        spell = repo.get(k)
        pack = repo.get_item_pack_id(k) or "srd"
        if selected_packs is None or pack in selected_packs:
            result.append(spell)
    return result


@router.get("/catalogs/spells/{index}")
async def get_spell(index: str) -> SpellDefinition:
    repo = container.spell_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Spell '{index}' not found") from e


# Monsters
@router.get("/catalogs/monsters")
async def list_monsters(keys_only: bool = False, packs: str | None = None) -> list[MonsterSheet] | list[str]:
    """List all monsters (full objects by default, or keys with ?keys_only=true).

    Args:
        keys_only: Return only keys instead of full objects
        packs: Comma-separated list of content pack IDs to filter by (e.g., "srd,custom1")
    """
    repo = container.monster_repository
    keys = repo.list_keys()
    if keys_only:
        return keys
    result: list[MonsterSheet] = []
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    for k in keys:
        monster = repo.get(k)
        pack = repo.get_item_pack_id(k) or "srd"
        if selected_packs is None or pack in selected_packs:
            result.append(monster)
    return result


@router.get("/catalogs/monsters/{index}")
async def get_monster(index: str) -> MonsterSheet:
    repo = container.monster_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Monster '{index}' not found") from e


# Magic Schools
@router.get("/catalogs/magic_schools")
async def list_magic_schools(keys_only: bool = False, packs: str | None = None) -> list[MagicSchool] | list[str]:
    repo = container.magic_school_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/magic_schools/{index}")
async def get_magic_school(index: str) -> MagicSchool:
    repo = container.magic_school_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Magic school '{index}' not found") from e


# Alignment
@router.get("/catalogs/alignments")
async def list_alignments(keys_only: bool = False, packs: str | None = None) -> list[Alignment] | list[str]:
    repo = container.alignment_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/alignments/{index}")
async def get_alignment(index: str) -> Alignment:
    repo = container.alignment_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Alignment '{index}' not found") from e


# Classes
@router.get("/catalogs/classes")
async def list_classes(keys_only: bool = False, packs: str | None = None) -> list[ClassDefinition] | list[str]:
    repo = container.class_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/classes/{index}")
async def get_class(index: str) -> ClassDefinition:
    repo = container.class_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Class '{index}' not found") from e


# Subclasses
@router.get("/catalogs/subclasses")
async def list_subclasses(keys_only: bool = False, packs: str | None = None) -> list[SubclassDefinition] | list[str]:
    repo = container.subclass_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/subclasses/{index}")
async def get_subclass(index: str) -> SubclassDefinition:
    repo = container.subclass_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Subclass '{index}' not found") from e


# Languages
@router.get("/catalogs/languages")
async def list_languages(keys_only: bool = False, packs: str | None = None) -> list[Language] | list[str]:
    repo = container.language_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/languages/{index}")
async def get_language(index: str) -> Language:
    repo = container.language_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Language '{index}' not found") from e


# Conditions
@router.get("/catalogs/conditions")
async def list_conditions(keys_only: bool = False, packs: str | None = None) -> list[Condition] | list[str]:
    repo = container.condition_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/conditions/{index}")
async def get_condition(index: str) -> Condition:
    repo = container.condition_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Condition '{index}' not found") from e


# Races
@router.get("/catalogs/races")
async def list_races(keys_only: bool = False, packs: str | None = None) -> list[RaceDefinition] | list[str]:
    repo = container.race_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/races/{index}")
async def get_race(index: str) -> RaceDefinition:
    repo = container.race_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Race '{index}' not found") from e


# Subraces
@router.get("/catalogs/race_subraces")
async def list_race_subraces(
    keys_only: bool = False, packs: str | None = None
) -> list[RaceSubraceDefinition] | list[str]:
    repo = container.race_subrace_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/race_subraces/{index}")
async def get_race_subrace(index: str) -> RaceSubraceDefinition:
    repo = container.race_subrace_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Race subrace '{index}' not found") from e


# Backgrounds
@router.get("/catalogs/backgrounds")
async def list_backgrounds(keys_only: bool = False, packs: str | None = None) -> list[BackgroundDefinition] | list[str]:
    repo = container.background_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/backgrounds/{index}")
async def get_background(index: str) -> BackgroundDefinition:
    repo = container.background_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Background '{index}' not found") from e


# Traits
@router.get("/catalogs/traits")
async def list_traits(keys_only: bool = False, packs: str | None = None) -> list[TraitDef] | list[str]:
    repo = container.trait_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/traits/{index}")
async def get_trait(index: str) -> TraitDef:
    repo = container.trait_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Trait '{index}' not found") from e


# Features
@router.get("/catalogs/features")
async def list_features(keys_only: bool = False, packs: str | None = None) -> list[FeatureDef] | list[str]:
    repo = container.feature_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/features/{index}")
async def get_feature(index: str) -> FeatureDef:
    repo = container.feature_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Feature '{index}' not found") from e


# Feats
@router.get("/catalogs/feats")
async def list_feats(keys_only: bool = False, packs: str | None = None) -> list[FeatDef] | list[str]:
    repo = container.feat_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/feats/{index}")
async def get_feat(index: str) -> FeatDef:
    repo = container.feat_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Feat '{index}' not found") from e


# Skills
@router.get("/catalogs/skills")
async def list_skills(keys_only: bool = False, packs: str | None = None) -> list[Skill] | list[str]:
    repo = container.skill_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/skills/{index}")
async def get_skill(index: str) -> Skill:
    repo = container.skill_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Skill '{index}' not found") from e


# Weapon Properties
@router.get("/catalogs/weapon_properties")
async def list_weapon_properties(keys_only: bool = False, packs: str | None = None) -> list[WeaponProperty] | list[str]:
    repo = container.weapon_property_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/weapon_properties/{index}")
async def get_weapon_property(index: str) -> WeaponProperty:
    repo = container.weapon_property_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Weapon property '{index}' not found") from e


# Damage Types
@router.get("/catalogs/damage_types")
async def list_damage_types(keys_only: bool = False, packs: str | None = None) -> list[DamageType] | list[str]:
    repo = container.damage_type_repository
    keys = repo.list_keys()
    selected_packs = [p.strip() for p in packs.split(",")] if packs else None
    if selected_packs is not None:
        keys = [k for k in keys if (repo.get_item_pack_id(k) or "srd") in selected_packs]
    if keys_only:
        return keys
    return [repo.get(k) for k in keys]


@router.get("/catalogs/damage_types/{index}")
async def get_damage_type(index: str) -> DamageType:
    repo = container.damage_type_repository
    try:
        return repo.get(index)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Damage type '{index}' not found") from e
