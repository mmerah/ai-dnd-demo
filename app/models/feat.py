from pydantic import BaseModel


class FeatDefinition(BaseModel):
    index: str
    name: str
    description: str | None = None
    prerequisites: str | None = None
