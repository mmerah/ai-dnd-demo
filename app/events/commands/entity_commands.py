"""Entity-related command definitions."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand
from app.models.attributes import EntityType


@dataclass
class UpdateHPCommand(BaseCommand):
    """Command to update entity hit points."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""  # required: instance id of target
    entity_type: EntityType = EntityType.PLAYER
    amount: int = 0  # negative for damage, positive for healing
    damage_type: str = "untyped"

    def get_handler_name(self) -> str:
        return "entity"


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
        return "entity"


@dataclass
class UpdateSpellSlotsCommand(BaseCommand):
    """Command to update entity spell slots."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""  # required: instance id of target
    entity_type: EntityType = EntityType.PLAYER
    level: int = 1
    amount: int = 0

    def get_handler_name(self) -> str:
        return "entity"


@dataclass
class LevelUpCommand(BaseCommand):
    """Command to level up an entity by one level."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""  # required: instance id of target
    entity_type: EntityType = EntityType.PLAYER

    def get_handler_name(self) -> str:
        return "entity"
