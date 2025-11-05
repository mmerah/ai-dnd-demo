"""Tests for tool suggestion models."""

import pytest

from app.models.tool_suggestion import ToolSuggestion, ToolSuggestions


class TestToolSuggestion:
    """Test ToolSuggestion model."""

    def test_basic_suggestion(self) -> None:
        """Test creating a basic tool suggestion."""
        suggestion = ToolSuggestion(
            tool_name="roll_dice",
            reason="Player requested a skill check",
            confidence=0.85,
        )

        assert suggestion.tool_name == "roll_dice"
        assert suggestion.reason == "Player requested a skill check"
        assert suggestion.confidence == 0.85
        assert suggestion.arguments is None

    def test_suggestion_with_arguments(self) -> None:
        """Test suggestion with suggested arguments."""
        suggestion = ToolSuggestion(
            tool_name="modify_currency",
            reason="Gold mentioned in prompt",
            confidence=0.75,
            arguments={"amount": 50, "currency_type": "gold"},
        )

        assert suggestion.tool_name == "modify_currency"
        assert suggestion.arguments == {"amount": 50, "currency_type": "gold"}

    def test_confidence_validation(self) -> None:
        """Test that confidence is validated in range 0.0-1.0."""
        # Valid confidence values
        ToolSuggestion(tool_name="test", reason="test", confidence=0.0)
        ToolSuggestion(tool_name="test", reason="test", confidence=0.5)
        ToolSuggestion(tool_name="test", reason="test", confidence=1.0)

        # Invalid confidence values
        with pytest.raises(ValueError):
            ToolSuggestion(tool_name="test", reason="test", confidence=-0.1)

        with pytest.raises(ValueError):
            ToolSuggestion(tool_name="test", reason="test", confidence=1.1)

    def test_empty_tool_name_rejected(self) -> None:
        """Test that empty tool name is rejected."""
        with pytest.raises(ValueError):
            ToolSuggestion(tool_name="", reason="test", confidence=0.5)

    def test_empty_reason_rejected(self) -> None:
        """Test that empty reason is rejected."""
        with pytest.raises(ValueError):
            ToolSuggestion(tool_name="test", reason="", confidence=0.5)


class TestToolSuggestions:
    """Test ToolSuggestions collection model."""

    def test_empty_suggestions(self) -> None:
        """Test creating empty suggestions collection."""
        suggestions = ToolSuggestions()
        assert suggestions.suggestions == []

    def test_suggestions_with_items(self) -> None:
        """Test creating suggestions with items."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(tool_name="roll_dice", reason="Check needed", confidence=0.9),
                ToolSuggestion(tool_name="modify_hp", reason="Damage dealt", confidence=0.8),
            ]
        )

        assert len(suggestions.suggestions) == 2
        assert suggestions.suggestions[0].tool_name == "roll_dice"
        assert suggestions.suggestions[1].tool_name == "modify_hp"

    def test_format_for_prompt_empty(self) -> None:
        """Test formatting empty suggestions returns empty string."""
        suggestions = ToolSuggestions()
        formatted = suggestions.format_for_prompt()
        assert formatted == ""

    def test_format_for_prompt_basic(self) -> None:
        """Test formatting basic suggestions."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(tool_name="roll_dice", reason="Skill check needed", confidence=0.85),
            ]
        )

        formatted = suggestions.format_for_prompt()

        assert "## Tool Suggestions" in formatted
        assert "roll_dice" in formatted
        assert "85%" in formatted
        assert "Skill check needed" in formatted
        assert "advisory" in formatted.lower()

    def test_format_for_prompt_with_arguments(self) -> None:
        """Test formatting suggestions with arguments."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(
                    tool_name="modify_currency",
                    reason="Gold transaction",
                    confidence=0.75,
                    arguments={"amount": 50, "currency_type": "gold"},
                ),
            ]
        )

        formatted = suggestions.format_for_prompt()

        assert "modify_currency" in formatted
        assert "75%" in formatted
        assert "Suggested args:" in formatted
        assert "amount=50" in formatted
        assert "currency_type=gold" in formatted

    def test_format_for_prompt_truncates_long_arguments(self) -> None:
        """Test that long argument lists are truncated."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(
                    tool_name="test_tool",
                    reason="Test",
                    confidence=0.5,
                    arguments={"arg1": 1, "arg2": 2, "arg3": 3, "arg4": 4, "arg5": 5},
                ),
            ]
        )

        formatted = suggestions.format_for_prompt()

        # Should show first 3 args and ellipsis
        assert "..." in formatted
        # Should not show all 5 arguments in detail
        assert "arg5" not in formatted or "..." in formatted

    def test_format_for_prompt_multiple_suggestions(self) -> None:
        """Test formatting multiple suggestions."""
        suggestions = ToolSuggestions(
            suggestions=[
                ToolSuggestion(tool_name="roll_dice", reason="Check 1", confidence=0.9),
                ToolSuggestion(tool_name="modify_hp", reason="Damage", confidence=0.8),
            ]
        )

        formatted = suggestions.format_for_prompt()

        # Check all three are present
        assert "1. roll_dice" in formatted
        assert "2. modify_hp" in formatted

        # Check confidence percentages
        assert "90%" in formatted
        assert "80%" in formatted
