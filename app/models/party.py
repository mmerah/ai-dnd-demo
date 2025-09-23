"""Party state models for managing NPC party members."""

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class PartyState(BaseModel):
    """State for managing party members (major NPCs that follow the player).

    Attributes:
        member_ids: List of NPC instance IDs that are in the party
        max_size: Maximum number of party members allowed (default 4)
    """

    member_ids: list[str] = Field(default_factory=list)
    max_size: int = Field(default=4, ge=1)

    @field_validator("member_ids")
    @classmethod
    def validate_member_count(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Ensure member_ids doesn't exceed max_size."""
        max_size = info.data.get("max_size", 4)
        if len(v) > max_size:
            raise ValueError(f"Party cannot have more than {max_size} members")
        return v

    def is_full(self) -> bool:
        """Check if the party is at maximum capacity."""
        return len(self.member_ids) >= self.max_size

    def has_member(self, npc_id: str) -> bool:
        """Check if an NPC is in the party."""
        return npc_id in self.member_ids

    def add_member(self, npc_id: str) -> None:
        """Add an NPC to the party if there's room and they're not already in it."""
        if self.is_full():
            raise ValueError(f"Party is full (max {self.max_size} members)")
        if self.has_member(npc_id):
            raise ValueError(f"NPC {npc_id} is already in the party")
        self.member_ids.append(npc_id)

    def remove_member(self, npc_id: str) -> None:
        """Remove an NPC from the party."""
        if not self.has_member(npc_id):
            raise ValueError(f"NPC {npc_id} is not in the party")
        self.member_ids.remove(npc_id)
