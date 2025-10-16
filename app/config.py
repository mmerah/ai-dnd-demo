"""Centralized configuration management for the application."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # OpenRouter API Configuration
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")

    # Agent-specific model configuration
    narrative_model: str = Field(..., alias="NARRATIVE_MODEL")
    combat_model: str = Field(..., alias="COMBAT_MODEL")
    summarizer_model: str = Field(..., alias="SUMMARIZER_MODEL")
    individual_npc_model: str = Field(..., alias="INDIVIDUAL_NPC_MODEL")
    puppeteer_npc_model: str = Field(..., alias="PUPPETEER_NPC_MODEL")

    # Retry Configuration
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Application Configuration
    save_directory: Path = Field(default=Path("./saves"), alias="SAVE_DIRECTORY")
    port: int = Field(default=8123, alias="PORT")

    # Debug Configuration
    debug_ai: bool = Field(default=False, alias="DEBUG_AI")
    debug_agent_context: bool = Field(default=False, alias="DEBUG_AGENT_CONTEXT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and ensure save directory exists."""
        super().__init__(**kwargs)
        # Ensure save directory exists
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def get_narrative_model(self) -> str:
        """Get the narrative agent model"""
        return self.narrative_model

    def get_combat_model(self) -> str:
        """Get the combat agent model"""
        return self.combat_model

    def get_summarizer_model(self) -> str:
        """Get the summarizer agent model"""
        return self.summarizer_model

    def get_individual_npc_model(self) -> str:
        """Get the individual NPC agent model"""
        return self.individual_npc_model

    def get_puppeteer_npc_model(self) -> str:
        """Get the puppeteer NPC agent model"""
        return self.puppeteer_npc_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the singleton settings instance."""
    return Settings()
