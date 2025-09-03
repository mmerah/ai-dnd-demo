from pydantic import BaseModel, Field


class ClassProficiencyChoice(BaseModel):
    choose: int
    from_options: list[str] = Field(default_factory=list)  # list of proficiency indexes


class ClassStartingEquipment(BaseModel):
    index: str
    quantity: int


class MultiClassingRequirement(BaseModel):
    ability: str
    minimum_score: int


class MultiClassingInfo(BaseModel):
    prerequisites: list[MultiClassingRequirement] = Field(default_factory=list)
    proficiencies: list[str] = Field(default_factory=list)
    proficiency_choices: list[ClassProficiencyChoice] = Field(default_factory=list)


class ClassDefinition(BaseModel):
    index: str
    name: str
    hit_die: int | None = None
    saving_throws: list[str] | None = None
    proficiencies: list[str] | None = None
    spellcasting_ability: str | None = None
    description: str | None = None
    proficiency_choices: list[ClassProficiencyChoice] | None = None
    starting_equipment: list[ClassStartingEquipment] | None = None
    starting_equipment_options_desc: list[str] | None = None
    subclasses: list[str] | None = None
    multi_classing: MultiClassingInfo | None = None


class SubclassDefinition(BaseModel):
    index: str
    name: str
    parent_class: str
    description: str | None = None
