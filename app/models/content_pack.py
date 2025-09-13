"""Content pack models for modular D&D content management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContentPackType(str, Enum):
    """Types of content packs.

    SRD: Base content in data/
    Custom: User-generated in user-data/
    Scenario: Scenario-specific in data/scenarios/<id>/...
    Sandbox: AI-Generated content during a game
    """

    SRD = "srd"
    CUSTOM = "custom"
    SCENARIO = "scenario"
    # TODO(MVP2): Support for on-the-fly AI-generated content
    SANDBOX = "sandbox"


class ContentPackMetadata(BaseModel):
    """Metadata for a content pack."""

    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    name: str
    version: str = "1.0.0"
    author: str
    description: str
    pack_type: ContentPackType = ContentPackType.CUSTOM
    dependencies: list[str] = Field(default_factory=lambda: ["srd"])
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def validate_dependencies(self, available_packs: list[str]) -> bool:
        """Validate that all dependencies are available.

        Args:
            available_packs: List of available pack IDs

        Returns:
            True if all dependencies are satisfied
        """
        return all(dep in available_packs for dep in self.dependencies)


class ContentPackSummary(BaseModel):
    """Summary information for a content pack."""

    id: str
    name: str
    version: str
    author: str
    description: str
    pack_type: ContentPackType


# TODO(MVP2): Implement load order
class ContentPackLoadOrder(BaseModel):
    """Defines the order in which content packs should be loaded."""

    pack_ids: list[str]

    def resolve_conflicts(self, item_key: str, sources: dict[str, str]) -> str:
        """Resolve conflicts when multiple packs define the same item.

        Args:
            item_key: The key of the conflicting item
            sources: Dictionary mapping pack_id to item definition

        Returns:
            The pack_id that should take precedence

        Raises:
            ValueError: If conflict cannot be resolved
        """
        # Later packs in the list override earlier ones
        for pack_id in reversed(self.pack_ids):
            if pack_id in sources:
                return pack_id

        raise ValueError(f"No valid source found for item '{item_key}'")
