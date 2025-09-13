from pydantic import BaseModel


class DamageType(BaseModel):
    index: str
    name: str
    description: str
    content_pack: str
