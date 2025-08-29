"""Service for converting between message formats following Single Responsibility."""

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from app.models.game_state import Message, MessageRole


class MessageConverterService:
    """Service for converting between message formats following Single Responsibility."""

    @staticmethod
    def to_pydantic_messages(messages: list[Message]) -> list[ModelMessage]:
        """Convert internal Message format to PydanticAI's ModelMessage format."""
        pydantic_messages: list[ModelMessage] = []

        for msg in messages:
            if msg.role == MessageRole.PLAYER:
                pydantic_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
            elif msg.role == MessageRole.DM:
                pydantic_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        return pydantic_messages
