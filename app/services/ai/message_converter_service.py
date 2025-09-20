"""Service for converting between message formats."""

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from app.agents.core.types import AgentType
from app.models.game_state import Message, MessageRole


class MessageConverterService:
    """Service for converting between message formats."""

    @staticmethod
    def to_pydantic_messages(messages: list[Message], agent_type: AgentType) -> list[ModelMessage]:
        """
        Convert internal Message format to PydanticAI's ModelMessage format.

        Args:
            messages: List of messages to convert
            agent_type: If provided, filter messages to only include those for this agent

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        pydantic_messages: list[ModelMessage] = []

        allowed_agent_types = {agent_type}
        if agent_type is AgentType.NARRATIVE:
            # Narrative agent needs to hear NPC conversations as well
            allowed_agent_types.add(AgentType.NPC)

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
