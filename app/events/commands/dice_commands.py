"""Dice-related command definitions."""

from dataclasses import dataclass

from app.events.base import BaseCommand


@dataclass
class RollDiceCommand(BaseCommand):
    """Command for any dice roll."""

    roll_type: str = ""  # 'ability_check', 'saving_throw', 'attack', 'damage', 'initiative'
    dice: str = "1d20"  # e.g., "1d20", "2d6"
    modifier: int = 0
    target: str | None = None
    ability: str | None = None
    skill: str | None = None
    damage_type: str | None = None

    # Optional field to directly apply a damage roll to an entity
    apply_to_entity_id: str | None = None
    apply_as_damage: bool = False
    apply_to_entity_type: str | None = None

    def get_handler_name(self) -> str:
        return "dice"
