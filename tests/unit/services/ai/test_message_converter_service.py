"""Tests for the MessageConverterService conversions."""

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agents.core.types import AgentType
from app.models.game_state import Message, MessageRole
from app.services.ai.message_converter_service import MessageConverterService
from tests.factories.game_state import make_game_state


def _first_part_content(model_message: ModelRequest | ModelResponse) -> str:
    assert model_message.parts, "Expected message to contain at least one part"
    for part in model_message.parts:
        if isinstance(part, TextPart | UserPromptPart):
            return str(part.content)
    raise ValueError("Message part has no textual content")


def test_narrative_history_includes_npc_dialogue() -> None:
    converter = MessageConverterService()
    game_state = make_game_state()
    messages = [
        Message(role=MessageRole.PLAYER, content="I scan the room.", agent_type=AgentType.NARRATIVE),
        Message(
            role=MessageRole.NPC,
            content="Morning, traveler!",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
    ]

    result = converter.to_pydantic_messages(
        messages=messages,
        agent_type=AgentType.NARRATIVE,
        game_state=game_state,
        npc_id="",
    )

    assert len(result) == 2
    assert isinstance(result[0], ModelRequest)
    assert _first_part_content(result[0]) == "I scan the room."
    assert isinstance(result[1], ModelResponse)
    assert _first_part_content(result[1]) == "Tom: Morning, traveler!"


def test_npc_history_keeps_other_npc_responses() -> None:
    converter = MessageConverterService()
    game_state = make_game_state()
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

    result = converter.to_pydantic_messages(
        messages=messages,
        agent_type=AgentType.NPC,
        game_state=game_state,
        npc_id="npc-123",
    )

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
    game_state = make_game_state()
    messages = [
        Message(
            role=MessageRole.NPC,
            content="Tom: Already noted.",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
    ]

    result = converter.to_pydantic_messages(
        messages=messages,
        agent_type=AgentType.NPC,
        game_state=game_state,
        npc_id="tom-id",
    )

    assert len(result) == 1
    assert isinstance(result[0], ModelResponse)
    assert _first_part_content(result[0]) == "Tom: Already noted."


def test_npc_in_party_sees_narrative_messages() -> None:
    """Test that NPCs in the party can see narrative DM messages."""
    converter = MessageConverterService()
    game_state = make_game_state()

    # Add NPC to party
    npc_id = "party-npc-123"
    game_state.party.member_ids.append(npc_id)

    messages = [
        Message(role=MessageRole.PLAYER, content="I look around.", agent_type=AgentType.NARRATIVE),
        Message(
            role=MessageRole.DM,
            content="You see a tavern ahead.",
            agent_type=AgentType.NARRATIVE,
        ),
        Message(
            role=MessageRole.NPC,
            content="I see it too!",
            agent_type=AgentType.NPC,
            speaker_npc_name="Tom",
        ),
    ]

    result = converter.to_pydantic_messages(
        messages=messages,
        agent_type=AgentType.NPC,
        game_state=game_state,
        npc_id=npc_id,
    )

    # NPC in party should see all three messages
    assert len(result) == 3
    assert isinstance(result[0], ModelRequest)
    assert _first_part_content(result[0]) == "I look around."
    assert isinstance(result[1], ModelResponse)
    assert _first_part_content(result[1]) == "You see a tavern ahead."
    assert isinstance(result[2], ModelResponse)
    assert _first_part_content(result[2]) == "Tom: I see it too!"


def test_npc_not_in_party_excludes_narrative_messages() -> None:
    """Test that NPCs not in the party do NOT see narrative DM messages."""
    converter = MessageConverterService()
    game_state = make_game_state()

    # NPC is NOT in party
    npc_id = "non-party-npc-456"

    messages = [
        Message(role=MessageRole.PLAYER, content="@Guard hello", agent_type=AgentType.NPC),
        Message(
            role=MessageRole.DM,
            content="The tavern is bustling.",
            agent_type=AgentType.NARRATIVE,
        ),
        Message(
            role=MessageRole.NPC,
            content="What do you want?",
            agent_type=AgentType.NPC,
            speaker_npc_name="Guard",
        ),
    ]

    result = converter.to_pydantic_messages(
        messages=messages,
        agent_type=AgentType.NPC,
        game_state=game_state,
        npc_id=npc_id,
    )

    # NPC not in party should NOT see narrative DM message
    assert len(result) == 2
    assert isinstance(result[0], ModelRequest)
    assert _first_part_content(result[0]) == "@Guard hello"
    assert isinstance(result[1], ModelResponse)
    assert _first_part_content(result[1]) == "Guard: What do you want?"
