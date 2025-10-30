"""Configuration loader for agent configurations and tool suggestion rules."""

import json
import logging
from pathlib import Path

from app.models.agent_config import AgentConfig
from app.models.tool_suggestion_config import ToolSuggestionRulesConfig

logger = logging.getLogger(__name__)


class AgentConfigValidationError(ValueError):
    """Raised when agent configuration is invalid."""

    pass


class AgentConfigLoader:
    """Loads and validates agent configurations from JSON files."""

    def __init__(self, config_dir: Path):
        """Initialize the config loader with a base directory.

        Args:
            config_dir: Path to directory containing agent configuration files
        """
        self.config_dir = config_dir
        logger.info(f"AgentConfigLoader initialized with config_dir: {config_dir}")

    def load_agent_config(self, filename: str) -> tuple[AgentConfig, str]:
        """Load and validate an agent configuration from a JSON file.

        Args:
            filename: Name of the JSON file (e.g., "narrative.json")

        Returns:
            Tuple of (validated AgentConfig instance, system prompt content)

        Raises:
            FileNotFoundError: If the config file or prompt file doesn't exist
            AgentConfigValidationError: If the config file is invalid
        """
        file_path = self.config_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Agent config file not found: {file_path}")

        try:
            with open(file_path) as f:
                data = json.load(f)

            config = AgentConfig.model_validate(data)

            # Load and validate the system prompt from the referenced markdown file
            prompt_file_path = self.config_dir / config.system_prompt_file
            if not prompt_file_path.exists():
                raise FileNotFoundError(
                    f"System prompt file not found: {prompt_file_path} " f"(referenced by {filename})"
                )

            with open(prompt_file_path) as f:
                system_prompt = f.read().strip()

            if not system_prompt:
                raise AgentConfigValidationError(f"System prompt file is empty: {prompt_file_path}")

            logger.info(
                f"Loaded agent config: {filename} (agent_type={config.agent_type}, "
                f"prompt={config.system_prompt_file}, {len(system_prompt)} chars)"
            )
            return config, system_prompt

        except json.JSONDecodeError as e:
            raise AgentConfigValidationError(f"Invalid JSON in {filename}: {e}") from e
        except FileNotFoundError:
            raise
        except Exception as e:
            raise AgentConfigValidationError(f"Failed to validate agent config {filename}: {e}") from e

    def load_tool_suggestion_rules(self) -> ToolSuggestionRulesConfig:
        """Load and validate tool suggestion rules configuration.

        Returns:
            Validated ToolSuggestionRulesConfig instance

        Raises:
            FileNotFoundError: If the rules config file doesn't exist
            ValueError: If the rules config is invalid
        """
        file_path = self.config_dir / "tool_suggestion_rules.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Tool suggestion rules file not found: {file_path}")

        try:
            with open(file_path) as f:
                data = json.load(f)

            config = ToolSuggestionRulesConfig.model_validate(data)
            enabled_rules = sum(1 for rule in config.rules if rule.enabled)
            logger.info(f"Loaded tool suggestion rules: {enabled_rules}/{len(config.rules)} rules enabled")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool_suggestion_rules.json: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to validate tool suggestion rules: {e}") from e
