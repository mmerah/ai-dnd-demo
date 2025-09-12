"""Commands for combat management."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand
from app.models.attributes import EntityType
from app.models.combat import MonsterSpawnInfo


@dataclass
class StartCombatCommand(BaseCommand):
    """Command to start combat with entity IDs."""

    agent_type: AgentType | None = field(default=None)
    entity_ids: list[str] = field(default_factory=list)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class StartEncounterCombatCommand(BaseCommand):
    """Command to trigger a predefined scenario encounter."""

    agent_type: AgentType | None = field(default=None)
    encounter_id: str = ""

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class SpawnMonstersCommand(BaseCommand):
    """Command to spawn monsters from database."""

    agent_type: AgentType | None = field(default=None)
    monsters: list[MonsterSpawnInfo] = field(default_factory=list)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class NextTurnCommand(BaseCommand):
    """Command to advance combat to the next turn."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class EndCombatCommand(BaseCommand):
    """Command to end the current combat encounter."""

    agent_type: AgentType | None = field(default=None)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class AddParticipantCommand(BaseCommand):
    """Add a participant (by entity id) to an existing combat."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""
    entity_type: EntityType = EntityType.MONSTER

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class RemoveParticipantCommand(BaseCommand):
    """Remove a participant from combat by entity id."""

    agent_type: AgentType | None = field(default=None)
    entity_id: str = ""

    def get_handler_name(self) -> str:
        return "combat"
