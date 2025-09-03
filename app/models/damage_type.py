from pydantic import BaseModel


class DamageType(BaseModel):
    index: str
    name: str
    description: str
