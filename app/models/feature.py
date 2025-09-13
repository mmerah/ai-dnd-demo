from pydantic import BaseModel


class FeatureGrantedBy(BaseModel):
    class_index: str
    subclass_index: str | None = None


class FeatureDefinition(BaseModel):
    index: str
    name: str
    description: str
    class_index: str
    subclass_index: str | None = None
    level: int
    granted_by: FeatureGrantedBy
    content_pack: str
