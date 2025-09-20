"""Tests for BaseNPCAgent message conversion."""

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agents.npc.base import BaseNPCAgent


class TestModelMessageToDict:
    """Test the _model_message_to_dict static method."""

    def test_converts_model_request_to_user_role(self) -> None:
        """Verify ModelRequest messages get 'user' role."""
        msg = ModelRequest(parts=[UserPromptPart(content="Hello NPC")])
        result = BaseNPCAgent._model_message_to_dict(msg)

        assert result["role"] == "user"
        assert result["content"] == "Hello NPC"

    def test_converts_model_response_to_assistant_role(self) -> None:
        """Verify ModelResponse messages get 'assistant' role."""
        msg = ModelResponse(parts=[TextPart(content="Greetings, traveler")])
        result = BaseNPCAgent._model_message_to_dict(msg)

        assert result["role"] == "assistant"
        assert result["content"] == "Greetings, traveler"

    def test_concatenates_multiple_parts(self) -> None:
        """Verify multiple text parts are concatenated."""
        msg = ModelResponse(parts=[TextPart(content="Part 1. "), TextPart(content="Part 2.")])
        result = BaseNPCAgent._model_message_to_dict(msg)

        assert result["content"] == "Part 1. Part 2."

    def test_handles_empty_parts_list(self) -> None:
        """Verify empty parts list is handled gracefully."""
        msg = ModelRequest(parts=[])
        result = BaseNPCAgent._model_message_to_dict(msg)

        assert result["role"] == "user"
        assert result["content"] == ""
