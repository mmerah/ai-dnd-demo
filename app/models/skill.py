from pydantic import BaseModel


class Skill(BaseModel):
    index: str
    name: str
    ability: str
    description: str | None = None
