from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from app.agents.core.base import BaseAgent
from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.models.ai_response import AIResponse
from app.models.combat import CombatSuggestion
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance
from app.models.scenario import ScenarioSheet
from app.models.tool_results import ToolResult
from app.models.tool_suggestion import ToolSuggestions


class IAIService(ABC):
    """Interface for the main AI service."""

    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        game_state: GameState,
        stream: bool = True,
    ) -> AsyncIterator[AIResponse]:
        """Generate AI response to user input via orchestration pipeline.

        The pipeline executes a series of steps:
        1. NPC dialogue detection and routing
        2. Agent selection (Narrative/Combat/NPC)
        3. Context building and tool suggestion enrichment
        4. Agent execution
        5. Combat transitions and auto-run loops
        6. State management

        Args:
            user_message: User's input message
            game_state: Current game state
            stream: Whether to stream response chunks (Note: SSE is source of truth)

        Yields:
            AIResponse objects (CompleteResponse, ErrorResponse, etc.)

        Raises:
            Exception: Any unhandled exception from pipeline execution (fail-fast)
        """
        pass


class IMessageService(ABC):
    """Interface for managing and broadcasting all game messages."""

    @abstractmethod
    async def send_narrative(
        self,
        game_id: str,
        content: str,
        is_chunk: bool = False,
        is_complete: bool = False,
    ) -> None:
        """Send narrative content via SSE.

        Args:
            game_id: ID of the game
            content: Narrative text content
            is_chunk: Whether this is a partial chunk
            is_complete: Whether the narrative is complete
        """
        pass

    @abstractmethod
    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, JSONSerializable]) -> None:
        """Broadcast a tool call event.

        Args:
            game_id: ID of the game
            tool_name: Name of the tool being called
            parameters: Tool parameters
        """
        pass

    @abstractmethod
    async def send_tool_result(self, game_id: str, tool_name: str, result: ToolResult) -> None:
        """Broadcast a tool result event.

        Args:
            game_id: ID of the game
            tool_name: Name of the tool that was called
            result: Tool execution result
        """
        pass

    @abstractmethod
    async def send_npc_dialogue(
        self,
        game_id: str,
        npc_id: str,
        npc_name: str,
        content: str,
        complete: bool = True,
    ) -> None:
        """Broadcast an NPC dialogue event."""
        pass

    @abstractmethod
    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        """Send error message via SSE.

        Args:
            game_id: ID of the game
            error: Error message
            error_type: Optional error type/category
        """
        pass

    @abstractmethod
    async def send_policy_warning(
        self, game_id: str, message: str, tool_name: str | None, agent_type: str | None
    ) -> None:
        """Send policy violation warning.

        Args:
            game_id: ID of the game
            message: Warning message
            tool_name: Optional tool that triggered warning
            agent_type: Optional agent type involved
        """
        pass

    @abstractmethod
    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        """Send complete game state update.

        Args:
            game_id: ID of the game
            game_state: Updated game state
        """
        pass

    @abstractmethod
    async def send_combat_suggestion(self, game_id: str, suggestion: CombatSuggestion) -> None:
        """Broadcast a combat suggestion from an allied NPC.

        Args:
            game_id: ID of the game
            suggestion: Combat suggestion with NPC action
        """
        pass

    @abstractmethod
    async def send_complete(self, game_id: str) -> None:
        """Send completion signal.

        Args:
            game_id: ID of the game
        """
        pass

    @abstractmethod
    def generate_sse_events(
        self,
        game_id: str,
        game_state: GameState,
        scenario: ScenarioSheet,
        available_scenarios: list[ScenarioSheet],
    ) -> AsyncGenerator[dict[str, str], None]:
        """Generate SSE events for game updates.

        Args:
            game_id: ID of the game
            game_state: Current game state
            scenario: Active scenario
            available_scenarios: List of available scenarios

        Yields:
            SSE event dictionaries with 'event' and 'data' keys
        """
        pass


class IContextService(ABC):
    """Interface for creating augmented context for AI prompting."""

    @abstractmethod
    def build_context(self, game_state: GameState, agent_type: AgentType) -> str:
        """Build context for AI agent.

        Args:
            game_state: Current game state
            agent_type: Type of agent requesting context

        Returns:
            Context string optimized for the specified agent type
        """
        pass

    @abstractmethod
    def build_context_for_npc(self, game_state: GameState, npc: NPCInstance) -> str:
        """Build shared context slice for NPC agents.

        Args:
            game_state: Current game state
            npc: The NPC instance to build context for

        Returns:
            Context string customized for the specified NPC
        """

    @abstractmethod
    def build_npc_persona(self, npc: NPCInstance) -> str:
        """Build persona description for a specific NPC."""


class IAgentLifecycleService(ABC):
    """Lifecycle management for dynamic NPC agents."""

    @abstractmethod
    def get_npc_agent(self, game_state: GameState, npc: NPCInstance) -> BaseAgent:
        """Return the agent that should speak for the given NPC."""

    @abstractmethod
    def release_npc_agent(self, game_id: str, npc_id: str) -> None:
        """Release cached agent state for a specific NPC."""

    @abstractmethod
    def release_for_game(self, game_id: str) -> None:
        """Clear all cached agents associated with a game."""


class IEventLoggerService(ABC):
    """Interface for logging agentic events."""

    @abstractmethod
    def set_game_id(self, game_id: str) -> None:
        """Set the current game ID for logging context.

        Args:
            game_id: ID of the game being processed
        """
        pass

    @abstractmethod
    def set_agent_type(self, agent_type: str) -> None:
        """Set the current agent type for logging context.

        Args:
            agent_type: Type of agent (narrative, combat, etc.)
        """
        pass

    @abstractmethod
    def log_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        """Log a tool call event.

        Args:
            tool_name: Name of the tool being called
            args: Arguments passed to the tool
        """
        pass

    @abstractmethod
    def log_tool_result(self, tool_name: str, result: str) -> None:
        """Log a tool result event.

        Args:
            tool_name: Name of the tool that was called
            result: String representation of the result
        """
        pass

    @abstractmethod
    def log_thinking(self, content: str) -> None:
        """Log agent thinking/reasoning content.

        Args:
            content: Thinking content to log
        """
        pass

    @abstractmethod
    def log_error(self, error: Exception) -> None:
        """Log an error event.

        Args:
            error: Exception that occurred
        """
        pass


class IToolCallExtractorService(ABC):
    """Interface for extracting and executing tool calls from narrative text."""

    @abstractmethod
    def extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        """Extract tool calls from narrative text.

        Args:
            text: The narrative text that may contain tool calls

        Returns:
            List of tool call dictionaries with 'function' and 'arguments' keys
        """
        pass

    @abstractmethod
    async def execute_extracted_tool_call(
        self,
        tool_call: dict[str, Any],
        game_state: GameState,
        agent_type: AgentType,
    ) -> bool:
        """Execute an extracted tool call.

        Args:
            tool_call: Dictionary with 'function' and 'arguments' keys
            game_state: Current game state
            agent_type: The agent type executing the tool

        Returns:
            True if tool was executed successfully, False otherwise
        """
        pass


class IToolSuggestionService(ABC):
    """Interface for tool suggestion service."""

    @abstractmethod
    async def suggest_tools(
        self,
        game_state: GameState,
        prompt: str,
        agent_type: str,
    ) -> ToolSuggestions:
        """Generate tool suggestions based on game state and user prompt.

        Args:
            game_state: Current game state
            prompt: User's prompt text
            agent_type: Type of agent being invoked (e.g., "narrative", "combat")

        Returns:
            ToolSuggestions object with filtered and ranked suggestions
        """
        pass
