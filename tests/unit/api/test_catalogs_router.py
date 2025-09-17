"""Unit tests for catalog router helper endpoints."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import pytest
from fastapi import HTTPException

from app.api.routers import catalogs
from app.common.exceptions import RepositoryNotFoundError
from app.container import container
from app.models.requests import ResolveNamesRequest
from tests.factories import make_game_state


class StubRepo:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.data = {
            f"{prefix}-alpha": f"{prefix}-alpha-name",
            f"{prefix}-custom": f"{prefix}-custom-name",
        }

    def list_keys(self) -> list[str]:
        return list(self.data)

    def get(self, index: str) -> str:
        if index not in self.data:
            raise RepositoryNotFoundError(index)
        return self.data[index]

    def get_name(self, index: str) -> str:
        return self.get(index)

    def get_item_pack_id(self, index: str) -> str | None:
        return "custom" if index.endswith("custom") else "srd"


@dataclass
class StubGameService:
    game_state: object

    def get_game(self, game_id: str) -> object:
        return self.game_state


class StubRepositoryFactory:
    def __init__(self, mapping: dict[str, StubRepo]) -> None:
        self.mapping = mapping

    def __getattr__(self, name: str) -> Callable[[object], StubRepo]:
        if name.startswith("get_") and name.endswith("_repository_for"):
            base = name[4:-15]
            attr = f"{base}_repository"
            repo = self.mapping[attr]

            def getter(_state: object, repo: StubRepo = repo) -> StubRepo:
                return repo

            return getter
        raise AttributeError(name)


@pytest.mark.asyncio
class TestCatalogsRouter:
    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.repo_attrs = [
            "item_repository",
            "spell_repository",
            "monster_repository",
            "magic_school_repository",
            "alignment_repository",
            "class_repository",
            "subclass_repository",
            "language_repository",
            "condition_repository",
            "race_repository",
            "race_subrace_repository",
            "background_repository",
            "feat_repository",
            "feature_repository",
            "trait_repository",
            "skill_repository",
            "weapon_property_repository",
            "damage_type_repository",
        ]
        self.originals = {
            name: getattr(container, name) for name in self.repo_attrs + ["game_service", "repository_factory"]
        }
        self.repos = {name: StubRepo(name.replace("_repository", "")) for name in self.repo_attrs}
        for name, repo in self.repos.items():
            setattr(container, name, repo)
        container.game_service = cast(Any, StubGameService(self.game_state))
        container.repository_factory = cast(Any, StubRepositoryFactory(self.repos))

        self.resolve_fields = {
            "items": "item_repository",
            "spells": "spell_repository",
            "monsters": "monster_repository",
            "classes": "class_repository",
            "races": "race_repository",
            "alignments": "alignment_repository",
            "backgrounds": "background_repository",
            "feats": "feat_repository",
            "features": "feature_repository",
            "traits": "trait_repository",
            "skills": "skill_repository",
            "conditions": "condition_repository",
            "languages": "language_repository",
            "damage_types": "damage_type_repository",
            "magic_schools": "magic_school_repository",
            "subclasses": "subclass_repository",
            "subraces": "race_subrace_repository",
            "weapon_properties": "weapon_property_repository",
        }

    def teardown_method(self) -> None:
        for name, value in self.originals.items():
            setattr(container, name, value)

    async def test_resolve_names_returns_known_values(self) -> None:
        payload: dict[str, list[str]] = {
            field: [f"{attr.replace('_repository', '')}-alpha", "missing"]
            for field, attr in self.resolve_fields.items()
        }
        request = ResolveNamesRequest(game_id=self.game_state.game_id, **payload)
        response = await catalogs.resolve_names(request)

        for field, attr in self.resolve_fields.items():
            key = f"{attr.replace('_repository', '')}-alpha"
            section = getattr(response, field)
            assert section[key] == self.repos[attr].get_name(key)
            assert "missing" not in section

    async def test_catalog_list_functions_respect_filters(self) -> None:
        endpoints = [
            (catalogs.list_items, catalogs.get_item, "item_repository"),
            (catalogs.list_spells, catalogs.get_spell, "spell_repository"),
            (catalogs.list_monsters, catalogs.get_monster, "monster_repository"),
            (catalogs.list_magic_schools, catalogs.get_magic_school, "magic_school_repository"),
            (catalogs.list_alignments, catalogs.get_alignment, "alignment_repository"),
            (catalogs.list_classes, catalogs.get_class, "class_repository"),
            (catalogs.list_subclasses, catalogs.get_subclass, "subclass_repository"),
            (catalogs.list_languages, catalogs.get_language, "language_repository"),
            (catalogs.list_conditions, catalogs.get_condition, "condition_repository"),
            (catalogs.list_races, catalogs.get_race, "race_repository"),
            (catalogs.list_race_subraces, catalogs.get_race_subrace, "race_subrace_repository"),
            (catalogs.list_backgrounds, catalogs.get_background, "background_repository"),
            (catalogs.list_feats, catalogs.get_feat, "feat_repository"),
            (catalogs.list_features, catalogs.get_feature, "feature_repository"),
            (catalogs.list_traits, catalogs.get_trait, "trait_repository"),
            (catalogs.list_skills, catalogs.get_skill, "skill_repository"),
            (catalogs.list_weapon_properties, catalogs.get_weapon_property, "weapon_property_repository"),
            (catalogs.list_damage_types, catalogs.get_damage_type, "damage_type_repository"),
        ]

        for list_func, get_func, attr in endpoints:
            repo = self.repos[attr]
            assert set(await list_func()) == set(repo.data.values())
            assert set(await list_func(keys_only=True)) == set(repo.data)
            assert await list_func(packs="custom") == [repo.data[f"{attr.replace('_repository', '')}-custom"]]

            key = f"{attr.replace('_repository', '')}-alpha"
            fetched = await get_func(key)
            assert cast(Any, fetched) == repo.data[key]
            with pytest.raises(HTTPException):
                await get_func("missing")
