"""Commands for combat management."""

from dataclasses import dataclass, field

from app.events.base import BaseCommand
from app.models.combat import CombatParticipant, MonsterSpawnInfo


@dataclass
class StartCombatCommand(BaseCommand):
    """Command to start general combat."""

    npcs: list[CombatParticipant] = field(default_factory=list)

    def get_handler_name(self) -> str:
        return "combat"


@dataclass
class TriggerScenarioEncounterCommand(BaseCommand):
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
