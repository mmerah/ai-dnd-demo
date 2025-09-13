from pydantic import BaseModel


class WeaponProperty(BaseModel):
    index: str
    name: str
    description: str
    content_pack: str
