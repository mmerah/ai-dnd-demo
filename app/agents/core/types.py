"""Types of specialized agents."""

from enum import Enum


class AgentType(Enum):
    """Types of specialized agents."""

    NARRATIVE = "narrative"
    COMBAT = "combat"
    SUMMARIZER = "summarizer"
    NPC = "npc"
    PLAYER = "player"
