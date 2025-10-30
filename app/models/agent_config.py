"""Agent configuration models for data-driven agent setup."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentModelConfig(BaseModel):
    """Model configuration settings for an agent."""

    temperature: float = Field(..., ge=0.0, le=2.0, description="Model temperature (0.0-2.0)")
    max_tokens: int = Field(..., gt=0, description="Maximum tokens for response")
    reasoning_effort: Literal["low", "medium", "high"] = Field(..., description="OpenAI reasoning effort level")
    parallel_tool_calls: bool = Field(..., description="Whether to allow parallel tool calls")


class AgentConfig(BaseModel):
    """Configuration for a single agent type."""

    agent_type: str = Field(..., description="Agent type identifier (e.g., 'narrative', 'combat')")
    description: str = Field(..., description="Human-readable description of agent's role")
    agent_model_config: AgentModelConfig = Field(..., description="Model-specific configuration")
    system_prompt_file: str = Field(..., min_length=1, description="Path to markdown file containing system prompt")


class AgentRegistry(BaseModel):
    """Registry of all agent configurations."""

    agents: dict[str, AgentConfig] = Field(default_factory=dict, description="Map of agent_type to configuration")
