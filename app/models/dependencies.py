"""Agent dependencies for PydanticAI tools."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.models.game_state import GameState
from app.services.dice_service import DiceService
from app.services.game_service import GameService

# Avoid circular import
if TYPE_CHECKING:
    from app.events.event_bus import EventBus


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent."""

    game_state: GameState
    game_service: GameService
    dice_service: DiceService
    event_bus: "EventBus"
