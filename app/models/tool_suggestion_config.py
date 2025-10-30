"""Tool suggestion configuration models for heuristic-based tool recommendations."""

from typing import Any

from pydantic import BaseModel, Field


class PatternConfig(BaseModel):
    """Regular expression pattern with weight for matching."""

    pattern: str = Field(..., min_length=1, description="Regex pattern to match")
    weight: float = Field(..., ge=0.0, le=1.0, description="Pattern match weight (0.0-1.0)")
    description: str | None = Field(None, description="Human-readable pattern description")


class SuggestionConfig(BaseModel):
    """Configuration for a tool suggestion."""

    tool_name: str = Field(..., min_length=1, description="Name of the tool to suggest")
    reason: str = Field(..., min_length=1, description="Reason for suggestion")
    confidence_multiplier: float = Field(default=1.0, ge=0.0, le=2.0, description="Multiplier for confidence (0.0-2.0)")
    suggested_args: dict[str, Any] | None = Field(None, description="Optional suggested arguments")


class RuleConfig(BaseModel):
    """Configuration for a single heuristic rule."""

    rule_id: str = Field(..., min_length=1, description="Unique rule identifier")
    rule_class: str = Field(..., min_length=1, description="Python class name for this rule")
    enabled: bool = Field(default=True, description="Whether this rule is active")
    description: str = Field(..., min_length=1, description="Human-readable rule description")
    patterns: list[PatternConfig] = Field(default_factory=list, description="Patterns to match")
    suggestions: list[SuggestionConfig] = Field(default_factory=list, description="Tools to suggest when matched")
    applicable_agents: list[str] = Field(default_factory=list, description="Agent types this rule applies to")
    required_context: list[str] | None = Field(None, description="Required game state context keys")
    state_check: str | None = Field(None, description="Game state condition to check")
    base_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Base confidence for this rule (0.0-1.0)")


class ToolSuggestionRulesConfig(BaseModel):
    """Root configuration for all tool suggestion rules."""

    rules: list[RuleConfig] = Field(default_factory=list, description="List of all rules")
    global_settings: dict[str, Any] = Field(default_factory=dict, description="Global configuration settings")
