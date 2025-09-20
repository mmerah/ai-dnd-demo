"""Tests for the MessageConverterService conversions."""

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agents.core.types import AgentType
from app.models.game_state import Message, MessageRole
from app.services.ai.message_converter_service import MessageConverterService


def _first_part_content(model_message: ModelRequest | ModelResponse) -> str:
    assert model_message.parts, "Expected message to contain at least one part"
    for part in model_message.parts:
        if isinstance(part, TextPart | UserPromptPart):
            return str(part.content)
    raise ValueError("Message part has no textual content")


def test_narrative_history_includes_npc_dialogue() -> None:
    converter = MessageConverterService()
    messages = [
        Message(role=MessageRole.PLAYER, content="I scan the room.", agent_type=AgentType.NARRATIVE),
        Message(
            role=MessageRole.NPC,
            content="Morning, traveler!",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
    ]

    result = converter.to_pydantic_messages(messages, AgentType.NARRATIVE)

    assert len(result) == 2
    assert isinstance(result[0], ModelRequest)
    assert _first_part_content(result[0]) == "I scan the room."
    assert isinstance(result[1], ModelResponse)
    assert _first_part_content(result[1]) == "Tom: Morning, traveler!"


def test_npc_history_keeps_other_npc_responses() -> None:
    converter = MessageConverterService()
    messages = [
        Message(role=MessageRole.PLAYER, content="@Tom hello", agent_type=AgentType.NPC),
        Message(
            role=MessageRole.NPC,
            content="Hello there!",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
        Message(
            role=MessageRole.NPC,
            content="Tom already said it all.",
            agent_type=AgentType.NPC,
            speaker_npc_name="Sara",
        ),
        Message(
            role=MessageRole.DM,
            content="The tavern grows quiet.",
            agent_type=AgentType.NARRATIVE,
        ),
    ]

    result = converter.to_pydantic_messages(messages, AgentType.NPC)

    # Narrative DM line should be filtered out for NPC agents
    assert len(result) == 3
    assert isinstance(result[0], ModelRequest)
    assert _first_part_content(result[0]) == "@Tom hello"
    assert isinstance(result[1], ModelResponse)
    assert _first_part_content(result[1]) == "Tom: Hello there!"
    assert isinstance(result[2], ModelResponse)
    assert _first_part_content(result[2]) == "Sara: Tom already said it all."


def test_speaker_prefix_not_duplicated() -> None:
    converter = MessageConverterService()
    messages = [
        Message(
            role=MessageRole.NPC,
            content="Tom: Already noted.",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
    ]

    result = converter.to_pydantic_messages(messages, AgentType.NPC)

    assert len(result) == 1
    assert isinstance(result[0], ModelResponse)
    assert _first_part_content(result[0]) == "Tom: Already noted."
