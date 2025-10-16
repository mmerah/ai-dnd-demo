"""Party management tools for D&D 5e AI Dungeon Master."""

import logging

from pydantic import BaseModel
from pydantic_ai import RunContext

from app.agents.core.dependencies import AgentDependencies
from app.events.commands.party_commands import AddPartyMemberCommand, RemovePartyMemberCommand
from app.tools.decorators import tool_handler

logger = logging.getLogger(__name__)


@tool_handler(AddPartyMemberCommand)
async def add_party_member(
    ctx: RunContext[AgentDependencies],
    npc_id: str,
) -> BaseModel:
    """Add a major NPC to the party.

    Major NPCs can join the party and will automatically follow the player between locations.
    They will participate as allies in combat encounters.

    Requirements:
    - NPC must be a major NPC (minor NPCs cannot join)
    - NPC must be at the same location as the player
    - Party must not be full (max 4 members)
    - Cannot be used during combat
    - Only available to narrative agent

    Args:
        npc_id: The ID of the NPC to add to the party

    Examples:
        - Add companion: npc_id="<npc-instance-id>"
        - Recruit ally: npc_id="lyra-swiftwind-instance-123"

    Returns:
        Success message with party size
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")


@tool_handler(RemovePartyMemberCommand)
async def remove_party_member(
    ctx: RunContext[AgentDependencies],
    npc_id: str,
) -> BaseModel:
    """Remove an NPC from the party.

    NPCs can leave the party voluntarily or be dismissed. They will remain at their
    current location and no longer auto-follow the player.

    Requirements:
    - NPC must be in the party
    - Cannot be used during combat
    - Only available to narrative agent

    Args:
        npc_id: The ID of the NPC to remove from the party

    Examples:
        - Companion leaves: npc_id="<npc-instance-id>"
        - Dismiss ally: npc_id="lyra-swiftwind-instance-123"

    Returns:
        Success message with updated party size
    """
    raise NotImplementedError("This is handled by the @tool_handler decorator")
