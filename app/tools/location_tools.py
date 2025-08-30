"""Location and navigation tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.dependencies import AgentDependencies
from app.events.commands.location_commands import (
    ChangeLocationCommand,
    DiscoverSecretCommand,
    UpdateLocationStateCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(ChangeLocationCommand)
async def change_location(ctx: RunContext[AgentDependencies], location_id: str) -> BaseModel:
    """Move to a connected location.

    Use when the player travels to a new area.

    Args:
        location_id: ID of the location to move to (must be connected)

    Examples:
        - Travel to forest: location_id="forest_path"
        - Enter cave: location_id="cave_entrance"
        - Return to tavern: location_id="tavern"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(DiscoverSecretCommand)
async def discover_secret(ctx: RunContext[AgentDependencies], secret_id: str) -> BaseModel:
    """Reveal a hidden secret or area.

    Use when the player discovers something hidden.

    Args:
        secret_id: ID of the secret discovered

    Examples:
        - Find hidden door: secret_id="hidden_door_1"
        - Discover cache: secret_id="treasure_cache"
        - Reveal inscription: secret_id="ancient_inscription"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(UpdateLocationStateCommand)
async def update_location_danger(ctx: RunContext[AgentDependencies], danger_level: str) -> BaseModel:
    """Update the danger level of the current location.

    Use when the threat level changes.

    Args:
        danger_level: New danger level (safe/low/moderate/high/extreme/cleared)

    Examples:
        - After defeating enemies: danger_level="cleared"
        - New threat arrives: danger_level="high"
        - Area becomes safe: danger_level="safe"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
