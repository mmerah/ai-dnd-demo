"""Location and navigation tools for D&D 5e AI Dungeon Master."""

import logging
from typing import Any

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
async def change_location(ctx: RunContext[AgentDependencies], location_id: str) -> dict[str, Any]:
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
async def discover_secret(ctx: RunContext[AgentDependencies], secret_id: str) -> dict[str, Any]:
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


async def search_location(ctx: RunContext[AgentDependencies], dc: int = 15) -> dict[str, Any]:
    """Search the current location for secrets and hidden items.

    Use when the player actively searches or investigates.

    Args:
        dc: Difficulty class for the search (default 15)

    Examples:
        - Search room thoroughly: dc=15
        - Quick glance around: dc=10
        - Detailed investigation: dc=20
    """
    deps = ctx.deps
    game_state = deps.game_state
    game_service = deps.game_service

    # Get current location state
    if not game_state.current_location_id:
        return {"success": False, "message": "No current location to search"}

    location_state = game_state.get_location_state(game_state.current_location_id)

    # Perform search (would normally roll dice)
    # For now, return available secrets based on DC
    discovered = []
    scenario = deps.scenario_service.get_scenario(game_state.scenario_id) if game_state.scenario_id else None

    if scenario:
        location = scenario.get_location(game_state.current_location_id)
        if location:
            for secret in location.secrets:
                if secret.id not in location_state.discovered_secrets and secret.dc and secret.dc <= dc:
                    discovered.append(secret.description)
                    location_state.discover_secret(secret.id)

    if discovered:
        game_service.save_game(game_state)
        return {"success": True, "discovered": discovered, "message": f"Found {len(discovered)} secret(s)!"}

    return {"success": False, "message": "Nothing unusual found"}


@tool_handler(UpdateLocationStateCommand)
async def update_location_danger(ctx: RunContext[AgentDependencies], danger_level: str) -> dict[str, Any]:
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
