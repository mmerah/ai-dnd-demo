"""OrchestrationContext and related types for pipeline execution."""

from dataclasses import dataclass, field, replace
from typing import Any

from app.agents.core.types import AgentType
from app.models.ai_response import StreamEvent
from app.models.game_state import GameState


@dataclass(frozen=True)
class OrchestrationFlags:
    """Flags for state transitions and special conditions used by pipeline guards."""

    combat_was_active: bool = False
    """Whether combat was active at the start of orchestration."""

    is_ally_turn: bool = False
    """Whether current turn is an allied NPC (for ally action wrapping)."""

    npc_targets: list[str] = field(default_factory=list)
    """List of NPC IDs targeted in the user message (e.g., @npc_name)."""

    # Duplicate detection tracking
    last_prompted_entity_id: str | None = None
    """Last entity ID prompted in combat loop (prevents duplicate prompts)."""

    last_prompted_round: int = 0
    """Last round number prompted in combat loop (prevents duplicate prompts)."""

    def with_updates(self, **kwargs: Any) -> "OrchestrationFlags":
        """Return a new instance with specified fields updated.

        Args:
            **kwargs: Fields to update

        Returns:
            New OrchestrationFlags with updates applied
        """
        return replace(self, **kwargs)


@dataclass(frozen=True)
class OrchestrationContext:
    """Immutable context carried through pipeline steps.

    Steps return updated copies via `with_updates()`. Note: game_state is mutable
    and modified by event handlers; use ReloadState to get fresh state.
    """

    # Immutable inputs
    user_message: str
    """The player's message/action being processed."""

    game_state: GameState
    """Current game state (mutable, event-sourced)."""

    game_id: str = field(init=False)
    """Game ID derived from game_state."""

    incoming_agent_hint: AgentType | None = None
    """Optional hint about which agent should handle this request."""

    # Agent selection and context
    selected_agent_type: AgentType | None = None
    """The agent type selected to handle this request."""

    context_text: str = ""
    """Accumulated context string to pass to the agent."""

    current_prompt: str = ""
    """Current combat prompt to be broadcast (used between Generate*Prompt and Broadcast*Prompt steps)."""

    # State tracking flags
    flags: OrchestrationFlags = field(default_factory=OrchestrationFlags)
    """Flags for state transitions and special conditions."""

    # Observability
    events: list[StreamEvent] = field(default_factory=list)
    """Stream events accumulated during pipeline execution."""

    def __post_init__(self) -> None:
        """Initialize derived fields."""
        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, "game_id", self.game_state.game_id)

    def with_updates(self, **kwargs: Any) -> "OrchestrationContext":
        """Return a new instance with specified fields updated.

        Args:
            **kwargs: Fields to update

        Returns:
            New OrchestrationContext with updates applied
        """
        return replace(self, **kwargs)

    def add_event(self, event: StreamEvent) -> "OrchestrationContext":
        """Return new context with event added to accumulated events."""
        return self.with_updates(events=[*self.events, event])

    def add_events(self, events: list[StreamEvent]) -> "OrchestrationContext":
        """Return new context with events added to accumulated events."""
        return self.with_updates(events=[*self.events, *events])

    def require_agent_type(self) -> AgentType:
        """Return selected agent type, raising ValueError if not set yet."""
        if self.selected_agent_type is None:
            raise ValueError("Agent type not selected - SelectAgent step must run first")
        return self.selected_agent_type
