"""Commands for combat management."""

from dataclasses import dataclass, field

from app.events.base import BaseCommand
from app.models.attributes import EntityType
from app.models.combat import MonsterSpawnInfo


@dataclass
class StartCombatCommand(BaseCommand):
    """Command to start combat with entity IDs."""

    entity_ids: list[str] = field(default_factory=list)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class StartEncounterCombatCommand(BaseCommand):
    """Command to trigger a predefined scenario encounter."""

    encounter_id: str = ""

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class SpawnMonstersCommand(BaseCommand):
    """Command to spawn monsters from database."""

    monsters: list[MonsterSpawnInfo] = field(default_factory=list)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class NextTurnCommand(BaseCommand):
    """Command to advance combat to the next turn."""

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class EndCombatCommand(BaseCommand):
    """Command to end the current combat encounter."""

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class AddParticipantCommand(BaseCommand):
    """Add a participant (by entity id) to an existing combat."""

    entity_id: str = ""
    entity_type: EntityType = EntityType.MONSTER

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class RemoveParticipantCommand(BaseCommand):
    """Remove a participant from combat by entity id."""

    entity_id: str = ""

    def get_handler_name(self) -> str:
        return "combat"
