"""Service for converting between message formats following Single Responsibility."""

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
    """Service for converting between message formats following Single Responsibility."""

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

        for msg in messages:
            # Filter by agent type if specified
            if msg.agent_type != agent_type:
                continue

            if msg.role == MessageRole.PLAYER:
                pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            elif msg.role == MessageRole.DM:
                pydantic_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        return pydantic_messages
