"""Dice-related command definitions."""

from dataclasses import dataclass, field

from app.agents.core.types import AgentType
from app.events.base import BaseCommand


@dataclass
class RollDiceCommand(BaseCommand):
    """Command for any dice roll."""

    agent_type: AgentType | None = field(default=None)
    roll_type: str = ""  # 'ability_check', 'saving_throw', 'attack', 'damage', 'initiative'
    dice: str = "1d20"  # e.g., "1d20", "2d6"
    modifier: int = 0
    ability: str | None = None
    skill: str | None = None

    def get_handler_name(self) -> str:
        return "dice"
