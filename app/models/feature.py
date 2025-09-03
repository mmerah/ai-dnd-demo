from pydantic import BaseModel


class FeatureGrantedBy(BaseModel):
    class_index: str | None = None
    subclass_index: str | None = None


class FeatureDefinition(BaseModel):
    index: str
    name: str
    description: str | None = None
    class_index: str | None = None
    subclass_index: str | None = None
    level: int | None = None
    granted_by: FeatureGrantedBy | None = None
