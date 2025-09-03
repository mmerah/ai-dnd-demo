from pydantic import BaseModel


class TraitDefinition(BaseModel):
    index: str
    name: str
    description: str
