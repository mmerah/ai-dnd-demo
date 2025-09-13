"""Repositories for class and subclass catalogs."""

from typing import Any

from app.interfaces.services.common import IContentPackRegistry, IPathResolver
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
    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "classes"

    def _parse_item(self, data: dict[str, Any]) -> ClassDefinition:
        """Parse raw item data into model instance."""
        return self._parse(data)

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
            hit_die=data["hit_die"],
            saving_throws=data["saving_throws"],
            proficiencies=data["proficiencies"],
            spellcasting_ability=data.get("spellcasting_ability"),
            description=data["description"],
            proficiency_choices=prof_choices,
            starting_equipment=starting_eq,
            starting_equipment_options_desc=data.get("starting_equipment_options_desc"),
            subclasses=data.get("subclasses"),
            multi_classing=mc,
            content_pack=data["content_pack"],
        )


class SubclassRepository(BaseRepository[SubclassDefinition]):
    def __init__(
        self,
        path_resolver: IPathResolver,
        cache_enabled: bool = True,
        content_pack_registry: IContentPackRegistry | None = None,
        content_packs: list[str] | None = None,
    ):
        super().__init__(cache_enabled, content_pack_registry, content_packs)
        self.path_resolver = path_resolver

    def _get_item_key(self, item_data: dict[str, Any]) -> str | None:
        """Extract the unique key from raw item data."""
        return str(item_data.get("index", ""))

    def _get_data_type(self) -> str:
        """Get the data type name for this repository."""
        return "subclasses"

    def _parse_item(self, data: dict[str, Any]) -> SubclassDefinition:
        """Parse raw item data into model instance."""
        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> SubclassDefinition:
        return SubclassDefinition(
            index=data["index"],
            name=data["name"],
            parent_class=data["parent_class"],
            description=data["description"],
            content_pack=data["content_pack"],
        )
