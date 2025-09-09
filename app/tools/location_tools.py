"""Location and navigation tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.location_commands import (
    ChangeLocationCommand,
    DiscoverSecretCommand,
    MoveNPCCommand,
    UpdateLocationStateCommand,
)
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(ChangeLocationCommand)
async def change_location(
    ctx: RunContext[AgentDependencies],
    location_id: str,
    location_name: str | None = None,
    description: str | None = None,
) -> BaseModel:
    """Move the party to a new location.

    Use when the player travels to any new area - scenario-defined, transitional, or custom.

    Location ID conventions:
    - Scenario locations: Use the exact ID from scenario (e.g., "tavern", "goblin-cave-entrance")
    - Transitional areas: Use descriptive IDs (e.g., "path-tavern-forest", "riverbank-crossing")
    - Custom locations: Use any meaningful ID (e.g., "hidden-grove", "abandoned-camp")

    Args:
        location_id: Unique identifier for the location
        location_name: Optional display name. Omit for scenario locations to use the scenario name.
        description: Optional description. Omit for scenario locations to use the scenario description.

    Examples:
        - Scenario location (auto): location_id="tavern"
        - Scenario location (override): location_id="tavern", description="You arrive from the back alley..."
        - Transitional: location_id="path-tavern-forest", location_name="Winding Path", description="You follow the dirt road..."
        - Custom: location_id="mysterious-clearing", location_name="Mysterious Clearing", description="You stumble upon..."
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
    complete_encounter: str | None = None,
    add_effect: str | None = None,
) -> BaseModel:
    """Update the state of the current location.

    Use this to reflect changes in the environment, such as clearing a room of enemies
    or a magical effect being applied to the area.

    Args:
        danger_level: New danger level (safe/low/moderate/high/extreme/cleared).
        complete_encounter: The ID of an encounter that has been resolved.
        add_effect: A new environmental effect to add (e.g., 'magical darkness', 'heavy fog').

    Examples:
        - After defeating enemies: danger_level="cleared", complete_encounter="goblin_guards"
        - A magical trap is sprung: add_effect="magical darkness"
        - Area becomes safer: danger_level="low"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(MoveNPCCommand)
async def move_npc_to_location(
    ctx: RunContext[AgentDependencies],
    npc_id: str,
    to_location_id: str,
) -> BaseModel:
    """Move an NPC to a different scenario location by ID.

    Args:
        npc_id: The NPC instance ID to move.
        to_location_id: The target location ID within the current scenario.

    Examples:
        - Move Tom the Barkeep to tavern: npc_id="<npc-instance-id>", to_location_id="tavern"
        - Send guard to cave entrance: npc_id="<guard-id>", to_location_id="goblin-cave-entrance"
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
