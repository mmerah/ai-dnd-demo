from pydantic import BaseModel


class Alignment(BaseModel):
    index: str
    name: str
    description: str
