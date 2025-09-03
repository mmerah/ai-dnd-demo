from pydantic import BaseModel


class BackgroundDefinition(BaseModel):
    index: str
    name: str
    description: str | None = None
