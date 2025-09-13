from pydantic import BaseModel


class MagicSchool(BaseModel):
    index: str
    name: str
    description: str
    content_pack: str
