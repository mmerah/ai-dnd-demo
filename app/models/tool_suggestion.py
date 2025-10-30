"""Tool suggestion models for runtime tool recommendations."""

from typing import Any

from pydantic import BaseModel, Field


class ToolSuggestion(BaseModel):
    """A suggestion to use a specific tool with reasoning and confidence."""

    tool_name: str = Field(..., min_length=1, description="Name of the suggested tool")
    reason: str = Field(..., min_length=1, description="Explanation for why this tool should be used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in this suggestion (0.0-1.0)")
    arguments: dict[str, Any] | None = Field(None, description="Optional suggested arguments for the tool")


class ToolSuggestions(BaseModel):
    """Collection of tool suggestions."""

    suggestions: list[ToolSuggestion] = Field(default_factory=list, description="List of tool suggestions")

    def format_for_prompt(self) -> str:
        """Format suggestions as markdown for inclusion in agent prompts.

        Returns:
            Markdown-formatted string with suggestions

        """
        if not self.suggestions:
            return ""

        lines: list[str] = ["## Tool Suggestions"]
        lines.append("")
        lines.append("Based on the current context, consider using these tools:")
        lines.append("")

        for i, suggestion in enumerate(self.suggestions, 1):
            confidence_percent = int(suggestion.confidence * 100)
            lines.append(f"**{i}. {suggestion.tool_name}** (confidence: {confidence_percent}%)")
            lines.append(f"   - Reason: {suggestion.reason}")
            if suggestion.arguments:
                args_preview = ", ".join(f"{k}={v}" for k, v in list(suggestion.arguments.items())[:3])
                if len(suggestion.arguments) > 3:
                    args_preview += ", ..."
                lines.append(f"   - Suggested args: {args_preview}")
            lines.append("")

        lines.append("*Note: These suggestions are advisory. Use your judgment to decide if they're appropriate.*")

        return "\n".join(lines)
