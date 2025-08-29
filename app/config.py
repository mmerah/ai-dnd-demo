"""Centralized configuration management for the application."""

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # OpenRouter API Configuration
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-oss-120b", alias="OPENROUTER_MODEL")

    # Retry Configuration
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Application Configuration
    save_directory: Path = Field(default=Path("./saves"), alias="SAVE_DIRECTORY")
    port: int = Field(default=8123, alias="PORT")

    # Debug Configuration
    debug_ai: bool = Field(default=False, alias="DEBUG_AI")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings and ensure save directory exists."""
        super().__init__(**kwargs)
        # Ensure save directory exists
        self.save_directory.mkdir(parents=True, exist_ok=True)


# Create singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
