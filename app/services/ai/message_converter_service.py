"""Service for converting between message formats."""

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from app.agents.core.types import AgentType
from app.models.game_state import GameState, Message, MessageRole


class MessageConverterService:
    """Service for converting between message formats."""

    @staticmethod
    def to_pydantic_messages(
        messages: list[Message],
        agent_type: AgentType,
        game_state: GameState,
        npc_id: str,
    ) -> list[ModelMessage]:
        """
        Convert internal Message format to PydanticAI's ModelMessage format.

        Args:
            messages: List of messages to convert
            agent_type: Agent type requesting the messages
            game_state: Current game state for party membership checks
            npc_id: NPC instance ID (required for NPC agents, use "" for others)

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        pydantic_messages: list[ModelMessage] = []

        allowed_agent_types = {agent_type}

        # Narrative agent includes NPC messages
        if agent_type is AgentType.NARRATIVE:
            allowed_agent_types.add(AgentType.NPC)

        # NPC agent includes Narrative messages ONLY if THIS specific NPC is in party
        if agent_type is AgentType.NPC and npc_id and npc_id in game_state.party.member_ids:
            allowed_agent_types.add(AgentType.NARRATIVE)

        for msg in messages:
            if msg.agent_type not in allowed_agent_types:
                continue

            if msg.role == MessageRole.PLAYER:
                pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            elif msg.role == MessageRole.NPC:
                speaker = msg.speaker_npc_name or msg.speaker_npc_id
                content = msg.content
                if speaker:
                    trimmed_content = content.lstrip()
                    prefix = f"{speaker}:"
                    if not trimmed_content.startswith(prefix):
                        content = f"{speaker}: {content}"
                pydantic_messages.append(ModelResponse(parts=[TextPart(content=content)]))
            elif msg.role == MessageRole.DM:
                pydantic_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        return pydantic_messages
