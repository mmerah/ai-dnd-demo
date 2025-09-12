"""Character-related command definitions."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand
from app.models.attributes import EntityType


@dataclass
class UpdateHPCommand(BaseCommand):
    """Command to update character or NPC hit points."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""  # required: instance id of target
    entity_type: EntityType = EntityType.PLAYER
    amount: int = 0  # negative for damage, positive for healing
    damage_type: str = "untyped"

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class UpdateConditionCommand(BaseCommand):
    """Command to add or remove a condition from a target."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""
    entity_type: EntityType = EntityType.PLAYER
    condition: str = ""
    action: str = "add"  # 'add' or 'remove'
    duration: int = 0

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class UpdateSpellSlotsCommand(BaseCommand):
    """Command to update spell slots."""

    agent_type: AgentType | None = field(default=None)
    level: int = 1
    amount: int = 0

    def get_handler_name(self) -> str:
        return "character"


@dataclass
class LevelUpCommand(BaseCommand):
    """Command to level up the player character by one level."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "character"
