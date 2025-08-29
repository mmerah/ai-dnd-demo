"""Commands for location and navigation management."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class ChangeLocationCommand(BaseCommand):
    """Command to change the current location."""

    location_id: str = ""
    location_name: str = ""
    description: str = ""

    def get_handler_name(self) -> str:
        return "location"


@dataclass
class DiscoverSecretCommand(BaseCommand):
    """Command to discover a secret in current location."""

    secret_id: str = ""
    secret_description: str = ""

    def get_handler_name(self) -> str:
        return "location"


@dataclass
class UpdateLocationStateCommand(BaseCommand):
    """Command to update location state."""

    location_id: str = ""
    danger_level: str | None = None
    add_npc: str | None = None
    remove_npc: str | None = None
    complete_encounter: str | None = None
    add_effect: str | None = None

    def get_handler_name(self) -> str:
        return "location"
