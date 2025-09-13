from pydantic import BaseModel


class BackgroundDefinition(BaseModel):
    index: str
    name: str
    description: str
    content_pack: str
