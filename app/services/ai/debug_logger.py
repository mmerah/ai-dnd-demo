"""Debug logging system for agent calls to track context and prompts."""

import json
import logging
from datetime import datetime
from pathlib import Path

from app.agents.core.types import AgentType

logger = logging.getLogger(__name__)


class AgentDebugLogger:
    """Logs detailed agent context for debugging."""

    def __init__(self, log_dir: Path = Path("logs"), enabled: bool = False):
        """Initialize debug logger.

        Args:
            log_dir: Directory to store agent logs
            enabled: Whether debug logging is enabled
        """
        self.log_dir = log_dir
        self.enabled = enabled
        self._log_files: dict[str, Path] = {}  # Cache of open log files per game_id

        if self.enabled:
            self.log_dir.mkdir(exist_ok=True)

    def _get_log_file_path(self, game_id: str) -> Path:
        """Get or create the log file path for a game session.

        Args:
            game_id: Game ID for this session

        Returns:
            Path to the log file for this game session
        """
        if game_id not in self._log_files:
            # Create filename based on game_id and session start time
            session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{game_id}_{session_time}.jsonl"  # Using JSON Lines format
            self._log_files[game_id] = self.log_dir / filename

            # Write header info when creating new file
            header = {
                "session_start": datetime.now().isoformat(),
                "game_id": game_id,
                "type": "session_header",
            }
            try:
                with open(self._log_files[game_id], "w") as f:
                    json.dump(header, f)
                    f.write("\n")
                logger.info(f"Created new agent debug log: {self._log_files[game_id]}")
            except Exception as e:
                logger.error(f"Failed to create agent debug log: {e}")

        return self._log_files[game_id]

    def log_agent_call(
        self,
        agent_type: AgentType,
        game_id: str,
        system_prompt: str,
        conversation_history: list[dict[str, str]],
        user_prompt: str,
        context: str,
    ) -> None:
        """Log detailed agent call information for debugging.

        Args:
            agent_type: Type of agent making the call
            game_id: Game ID for this session
            system_prompt: System prompt used for the agent
            conversation_history: Message history provided to agent
            user_prompt: User's input prompt
            context: Built context included in prompt
        """
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        log_entry = {
            "type": "agent_call",
            "timestamp": timestamp,
            "agent_type": agent_type.value,
            "game_id": game_id,
            "system_prompt": system_prompt[:200],  # Truncate very long prompts
            "conversation_history": [
                {
                    "role": msg.get("role", "unknown"),
                    "content": msg.get("content", "")[:500],  # Truncate for readability
                }
                for msg in conversation_history[-20:]  # Keep only last 20 messages
            ],
            "context": context[:2000],  # Truncate very long context
            "user_prompt": user_prompt,
        }

        try:
            log_path = self._get_log_file_path(game_id)

            # Append to existing file (JSON Lines format - one JSON object per line)
            with open(log_path, "a") as f:
                json.dump(log_entry, f, default=str)
                f.write("\n")

            logger.debug(f"Agent call appended to {log_path}")
        except Exception as e:
            logger.error(f"Failed to write agent debug log: {e}")
