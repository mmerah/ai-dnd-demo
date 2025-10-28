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
        self._log_files: dict[tuple[str, str, str | None], Path] = {}  # Cache per (game_id, agent_type, npc_id)

        if self.enabled:
            self.log_dir.mkdir(exist_ok=True)

    def _get_log_file_path(self, game_id: str, agent_type: str, npc_instance_id: str | None = None) -> Path:
        """Get or create the log file path for a game session and agent type.

        Args:
            game_id: Game ID for this session
            agent_type: Type of agent (narrative, combat, npc, summarizer)
            npc_instance_id: Optional NPC instance ID for individual NPC agents

        Returns:
            Path to the log file for this game session and agent type
        """
        cache_key = (game_id, agent_type, npc_instance_id)

        if cache_key not in self._log_files:
            # Create agent-specific filename
            if agent_type == "npc" and npc_instance_id:
                # Individual NPC agent: {game_id}_npc_{npc_instance_id}.jsonl
                filename = f"{game_id}_npc_{npc_instance_id}.jsonl"
            elif agent_type == "npc":
                # Puppeteer agent: {game_id}_npc_puppeteer.jsonl
                filename = f"{game_id}_npc_puppeteer.jsonl"
            else:
                # Other agents: {game_id}_{agent_type}.jsonl
                filename = f"{game_id}_{agent_type}.jsonl"

            self._log_files[cache_key] = self.log_dir / filename

            # Write header info when creating new file
            header = {
                "session_start": datetime.now().isoformat(),
                "game_id": game_id,
                "agent_type": agent_type,
                "type": "session_header",
            }
            if npc_instance_id:
                header["npc_instance_id"] = npc_instance_id

            try:
                with open(self._log_files[cache_key], "w") as f:
                    json.dump(header, f)
                    f.write("\n")
                logger.info(f"Created new agent debug log: {self._log_files[cache_key]}")
            except Exception as e:
                logger.error(f"Failed to create agent debug log: {e}")

        return self._log_files[cache_key]

    def log_agent_call(
        self,
        agent_type: AgentType,
        game_id: str,
        system_prompt: str,
        conversation_history: list[dict[str, str]],
        user_prompt: str,
        context: str,
        npc_instance_id: str | None = None,
    ) -> None:
        """Log detailed agent call information for debugging.

        Args:
            agent_type: Type of agent making the call
            game_id: Game ID for this session
            system_prompt: System prompt used for the agent
            conversation_history: Message history provided to agent
            user_prompt: User's input prompt
            context: Built context included in prompt
            npc_instance_id: Optional NPC instance ID for individual NPC agents
        """
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()

        # Truncate system prompt, limit message history for readability. Full context for debug.
        # VSCode Extension recommanded: toiroakr.jsonl-editor (displays text as multiline strings)
        log_entry = {
            "type": "agent_call",
            "timestamp": timestamp,
            "agent_type": agent_type.value,
            "game_id": game_id,
            "system_prompt": system_prompt[:200],
            "conversation_history": [
                {
                    "role": msg.get("role", "unknown"),
                    "content": msg.get("content", "")[:500],
                }
                for msg in conversation_history[-10:]
            ],
            "context": context,
            "user_prompt": user_prompt,
        }

        if npc_instance_id:
            log_entry["npc_instance_id"] = npc_instance_id

        try:
            log_path = self._get_log_file_path(game_id, agent_type.value, npc_instance_id)

            # Append to existing file (JSON Lines format - one JSON object per line)
            with open(log_path, "a") as f:
                json.dump(log_entry, f, default=str)
                f.write("\n")

            logger.debug(f"Agent call appended to {log_path}")
        except Exception as e:
            logger.error(f"Failed to write agent debug log: {e}")
