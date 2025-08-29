"""Commands for combat management."""

from dataclasses import dataclass, field

from app.events.base import BaseCommand


@dataclass
class StartCombatCommand(BaseCommand):
    """Command to start general combat."""

    npcs: list[dict[str, str | int]] = field(
        default_factory=list
    )  # List of NPC definitions with name and optional initiative

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

    monsters: list[dict[str, int]] = field(default_factory=list)  # Dict of monster_name: quantity

    def get_handler_name(self) -> str:
        return "combat"
