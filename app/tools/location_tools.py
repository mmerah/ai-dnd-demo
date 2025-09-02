"""Location and navigation tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
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
async def update_location_state(
    ctx: RunContext[AgentDependencies],
    danger_level: str | None = None,
    add_npc: str | None = None,
    remove_npc: str | None = None,
    complete_encounter: str | None = None,
    add_effect: str | None = None,
) -> BaseModel:
    """Update the state of the current location.

    Use this to reflect changes in the environment, such as clearing a room of enemies,
    an NPC arriving or leaving, or a magical effect being applied to the area.

    Args:
        danger_level: New danger level (safe/low/moderate/high/extreme/cleared).
        add_npc: The name of an NPC that has arrived at the location.
        remove_npc: The name of an NPC that has left the location.
        complete_encounter: The ID of an encounter that has been resolved.
        add_effect: A new environmental effect to add (e.g., 'magical darkness', 'heavy fog').

    Examples:
        - After defeating enemies: danger_level="cleared", complete_encounter="goblin_guards"
        - An ally arrives: add_npc="Elara"
        - A magical trap is sprung: add_effect="magical darkness"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
