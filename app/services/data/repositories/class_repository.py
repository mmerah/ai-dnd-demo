"""Repositories for class and subclass catalogs."""

from typing import Any

from app.interfaces.services import IPathResolver
from app.models.class_definitions import (
    ClassDefinition,
    ClassProficiencyChoice,
    ClassStartingEquipment,
    MultiClassingInfo,
    MultiClassingRequirement,
    SubclassDefinition,
)
from app.services.data.repositories.base_repository import BaseRepository


class ClassRepository(BaseRepository[ClassDefinition]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("classes")

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return
        for item in data.get("classes", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> ClassDefinition | None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return None
        for item in data.get("classes", []):
            if item.get("index") == key or (item.get("name") or "").lower() == key.lower():
                try:
                    return self._parse(item)
                except Exception:
                    return None
        return None

    def _get_all_keys(self) -> list[str]:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("classes", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return False
        for item in data.get("classes", []):
            if item.get("index") == key:
                return True
            if (item.get("name") or "").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> ClassDefinition:
        # Map nested optional structures if present
        prof_choices = None
        if isinstance(data.get("proficiency_choices"), list):
            prof_choices = [
                ClassProficiencyChoice(choose=pc.get("choose", 0), from_options=pc.get("from_options", []))
                for pc in data.get("proficiency_choices", [])
                if isinstance(pc, dict)
            ]
        starting_eq = None
        if isinstance(data.get("starting_equipment"), list):
            starting_eq = []
            for it in data.get("starting_equipment", []) or []:
                if isinstance(it, dict):
                    idx = it.get("index")
                    qty = it.get("quantity", 1)
                    if isinstance(idx, str):
                        try:
                            q = int(qty)
                        except Exception:
                            q = 1
                        starting_eq.append(ClassStartingEquipment(index=idx, quantity=q))
        mc = None
        if isinstance(data.get("multi_classing"), dict):
            raw = data["multi_classing"]
            prereqs: list[MultiClassingRequirement] = []
            for r in raw.get("prerequisites", []) or []:
                if isinstance(r, dict):
                    ability_obj = r.get("ability") or r.get("ability_score")
                    ability_index = (
                        ability_obj.get("index")
                        if isinstance(ability_obj, dict)
                        else (ability_obj if isinstance(ability_obj, str) else None)
                    )
                    if isinstance(ability_index, str):
                        try:
                            min_score = int(r.get("minimum_score", 0))
                        except Exception:
                            min_score = 0
                        prereqs.append(MultiClassingRequirement(ability=ability_index, minimum_score=min_score))
            mc_prof_choices: list[ClassProficiencyChoice] = []
            for pc in raw.get("proficiency_choices", []) or []:
                if isinstance(pc, dict):
                    mc_prof_choices.append(
                        ClassProficiencyChoice(choose=pc.get("choose", 0), from_options=pc.get("from_options", []))
                    )
            mc = MultiClassingInfo(
                prerequisites=prereqs,
                proficiencies=raw.get("proficiencies", []),
                proficiency_choices=mc_prof_choices,
            )

        return ClassDefinition(
            index=data["index"],
            name=data["name"],
            hit_die=data.get("hit_die"),
            saving_throws=data.get("saving_throws"),
            proficiencies=data.get("proficiencies"),
            spellcasting_ability=data.get("spellcasting_ability"),
            description=data.get("description"),
            proficiency_choices=prof_choices,
            starting_equipment=starting_eq,
            starting_equipment_options_desc=data.get("starting_equipment_options_desc"),
            subclasses=data.get("subclasses"),
            multi_classing=mc,
        )


class SubclassRepository(BaseRepository[SubclassDefinition]):
    def __init__(self, path_resolver: IPathResolver, cache_enabled: bool = True):
        super().__init__(cache_enabled)
        self.path_resolver = path_resolver
        self.file = self.path_resolver.get_shared_data_file("subclasses")

    def _initialize(self) -> None:
        if self.cache_enabled:
            self._load_all()
        self._initialized = True

    def _load_all(self) -> None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return
        for item in data.get("subclasses", []):
            try:
                model = self._parse(item)
                self._cache[model.index] = model
            except Exception:
                continue

    def _load_item(self, key: str) -> SubclassDefinition | None:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return None
        for item in data.get("subclasses", []):
            if item.get("index") == key or (item.get("name") or "").lower() == key.lower():
                try:
                    return self._parse(item)
                except Exception:
                    return None
        return None

    def _get_all_keys(self) -> list[str]:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return []
        return sorted([i.get("index", "") for i in data.get("subclasses", []) if i.get("index")])

    def _check_key_exists(self, key: str) -> bool:
        data = self._load_json_file(self.file)
        if not isinstance(data, dict):
            return False
        for item in data.get("subclasses", []):
            if item.get("index") == key:
                return True
            if (item.get("name") or "").lower() == key.lower():
                return True
        return False

    def _parse(self, data: dict[str, Any]) -> SubclassDefinition:
        return SubclassDefinition(
            index=data["index"],
            name=data["name"],
            parent_class=data["parent_class"],
            description=data.get("description"),
        )
