"""Pydantic schemas for content pack API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.content_pack import ContentPackSummary


class ContentPackListResponse(BaseModel):
    packs: list[ContentPackSummary]
    total: int


class ContentPackDetailResponse(BaseModel):
    id: str
    name: str
    version: str
    author: str
    description: str
    pack_type: str
    dependencies: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ValidatePacksRequest(BaseModel):
    pack_ids: list[str] = Field(min_length=1)


class ValidatePacksResponse(BaseModel):
    valid: bool
    error: str = ""
    ordered_packs: list[str] = Field(default_factory=list)
