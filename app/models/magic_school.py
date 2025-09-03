from pydantic import BaseModel


class MagicSchool(BaseModel):
    index: str
    name: str
    description: str | None = None
