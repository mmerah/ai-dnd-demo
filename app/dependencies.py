"""Centralized dependency management and instantiation."""

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from app.events.handlers.broadcast_handler import BroadcastHandler
from app.events.handlers.character_handler import CharacterHandler
from app.events.handlers.dice_handler import DiceHandler
from app.events.handlers.inventory_handler import InventoryHandler
from app.events.handlers.time_handler import TimeHandler
from app.models.game_state import GameState
from app.services.ai_service import AIService
from app.services.dice_service import DiceService
from app.services.game_service import GameService
from app.services.scenario_service import ScenarioService

# Use TYPE_CHECKING to avoid circular import at runtime
if TYPE_CHECKING:
    from app.events.event_bus import EventBus


@dataclass
class AgentDependencies:
    """Dependencies for the AI agent tools."""

    game_state: GameState
    game_service: GameService
    dice_service: DiceService
    event_bus: "EventBus"


# --- Singleton Service Providers ---


@lru_cache(maxsize=1)
def get_game_service() -> GameService:
    """Get the singleton GameService instance."""
    return GameService()


@lru_cache(maxsize=1)
def get_scenario_service() -> ScenarioService:
    """Get the singleton ScenarioService instance."""
    return ScenarioService()


@lru_cache(maxsize=1)
def get_dice_service() -> DiceService:
    """Get the singleton DiceService instance."""
    return DiceService()


@lru_cache(maxsize=1)
def get_event_bus() -> "EventBus":
    """Get the singleton EventBus instance, configured with all handlers."""
    # Import here to break circular dependency chain
    from app.events.event_bus import EventBus

    game_service = get_game_service()
    dice_service = get_dice_service()

    event_bus = EventBus(game_service)

    # Register all handlers
    event_bus.register_handler("character", CharacterHandler(game_service))
    event_bus.register_handler("dice", DiceHandler(game_service, dice_service))
    event_bus.register_handler("inventory", InventoryHandler(game_service))
    event_bus.register_handler("time", TimeHandler(game_service))
    event_bus.register_handler("broadcast", BroadcastHandler(game_service))

    return event_bus


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """Get the singleton AIService instance."""
    # Must be defined here to break circular dependencies
    # AIService -> EventBus -> Handlers -> Commands -> Tools -> Agent -> AIService
    from app.agents.factory import AgentFactory
    from app.agents.types import AgentType
    from app.config import get_settings

    settings = get_settings()
    event_bus = get_event_bus()
    game_service = get_game_service()

    # This creates a partial AIService, which we then configure
    ai_service = AIService(game_service)
    ai_service.narrative_agent = AgentFactory.create_agent(
        AgentType.NARRATIVE, event_bus=event_bus, debug=settings.debug_ai
    )
    return ai_service
