"""Agent dependencies for PydanticAI tools."""

from dataclasses import dataclass

from app.models.game_state import GameState
from app.services.dice_service import DiceService
from app.services.game_service import GameService


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent."""

    game_state: GameState
    game_service: GameService
    dice_service: DiceService
