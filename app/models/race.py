from pydantic import BaseModel, Field

from app.models.ability import AbilityBonuses


class RaceDefinition(BaseModel):
    index: str
    name: str
    speed: int
    size: str
    languages: list[str] = Field(default_factory=list)
    description: str | None = None
    traits: list[str] | None = None
    subraces: list[str] | None = None
    ability_bonuses: AbilityBonuses | None = None
    weapon_proficiencies: list[str] | None = None
    tool_proficiencies: list[str] | None = None
    language_options: list[str] | None = None


class SubraceDefinition(BaseModel):
    index: str
    name: str
    parent_race: str
    description: str | None = None
    traits: list[str] | None = None
    ability_bonuses: AbilityBonuses | None = None
    weapon_proficiencies: list[str] | None = None
    tool_proficiencies: list[str] | None = None
