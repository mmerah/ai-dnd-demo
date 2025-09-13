from pydantic import BaseModel


class Condition(BaseModel):
    index: str
    name: str
    description: str
    content_pack: str
