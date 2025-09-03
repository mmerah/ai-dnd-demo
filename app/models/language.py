from pydantic import BaseModel


class Language(BaseModel):
    index: str
    name: str
    type: str | None = None
    script: str | None = None
    description: str | None = None
