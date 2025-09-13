from pydantic import BaseModel


class FeatDefinition(BaseModel):
    index: str
    name: str
    description: str
    prerequisites: str | None = None
    content_pack: str
