"""Game state models for D&D 5e game session management."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .character import CharacterSheet
from .npc import NPCSheet

# Type alias for JSON-serializable data
# Note: We use Any here to avoid recursive type issues with Pydantic
# All actual data is validated through Pydantic models
JSONSerializable = str | int | float | bool | None | dict[str, Any] | list[Any]


class MessageRole(str, Enum):
    """Message sender role."""

    PLAYER = "player"
    DM = "dm"


class Message(BaseModel):
    """Chat message in game history - narrative only."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_type: str = "narrative"
    location: str | None = None
    npcs_mentioned: list[str] = Field(default_factory=list)
    combat_round: int | None = None


class GameEventType(str, Enum):
    """Types of game events."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DICE_ROLL = "dice_roll"
    STATE_CHANGE = "state_change"


class GameEvent(BaseModel):
    """Game mechanics event - separate from narrative."""

    event_type: GameEventType
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_name: str | None = None
    parameters: dict[str, JSONSerializable] | None = None
    result: JSONSerializable | None = None  # Can be dict, str, or other types
    metadata: dict[str, JSONSerializable] | None = None  # Additional context


class GameTime(BaseModel):
    """In-game time tracking."""

    day: int = Field(ge=1, default=1)
    hour: int = Field(ge=0, le=23, default=12)
    minute: int = Field(ge=0, le=59, default=0)

    def advance_minutes(self, minutes: int) -> None:
        """Advance game time by specified minutes."""
        total_minutes = self.hour * 60 + self.minute + minutes

        # Calculate new time
        days_passed = total_minutes // (24 * 60)
        remaining_minutes = total_minutes % (24 * 60)

        self.day += days_passed
        self.hour = remaining_minutes // 60
        self.minute = remaining_minutes % 60

    def advance_hours(self, hours: int) -> None:
        """Advance game time by specified hours."""
        self.advance_minutes(hours * 60)

    def short_rest(self) -> None:
        """Advance time for a short rest (1 hour)."""
        self.advance_hours(1)

    def long_rest(self) -> None:
        """Advance time for a long rest (8 hours)."""
        self.advance_hours(8)

    def to_string(self) -> str:
        """Get human-readable time string."""
        hour_12 = self.hour % 12 if self.hour % 12 != 0 else 12
        am_pm = "AM" if self.hour < 12 else "PM"
        return f"Day {self.day}, {hour_12}:{self.minute:02d} {am_pm}"


class CombatParticipant(BaseModel):
    """Participant in combat with initiative."""

    name: str
    initiative: int
    is_player: bool = False
    is_active: bool = True
    conditions: list[str] = Field(default_factory=list)


class CombatState(BaseModel):
    """Combat encounter state."""

    round_number: int = Field(ge=1, default=1)
    turn_index: int = Field(ge=0, default=0)
    participants: list[CombatParticipant] = Field(default_factory=list)
    is_active: bool = True

    def add_participant(self, name: str, initiative: int, is_player: bool = False) -> None:
        """Add a participant to combat."""
        participant = CombatParticipant(name=name, initiative=initiative, is_player=is_player)
        self.participants.append(participant)
        self.sort_by_initiative()

    def sort_by_initiative(self) -> None:
        """Sort participants by initiative (highest first)."""
        self.participants.sort(key=lambda p: p.initiative, reverse=True)

    def get_current_turn(self) -> CombatParticipant | None:
        """Get the participant whose turn it is."""
        active_participants = [p for p in self.participants if p.is_active]
        if not active_participants:
            return None

        # Ensure turn index is within bounds
        if self.turn_index >= len(active_participants):
            self.turn_index = 0

        return active_participants[self.turn_index]

    def next_turn(self) -> None:
        """Advance to next turn in combat."""
        active_participants = [p for p in self.participants if p.is_active]
        if not active_participants:
            self.is_active = False
            return

        self.turn_index += 1

        # Check if we've completed a round
        if self.turn_index >= len(active_participants):
            self.turn_index = 0
            self.round_number += 1

    def remove_participant(self, name: str) -> None:
        """Remove a participant from combat."""
        self.participants = [p for p in self.participants if p.name != name]

        # Adjust turn index if needed
        active_participants = [p for p in self.participants if p.is_active]
        if self.turn_index >= len(active_participants):
            self.turn_index = 0

    def end_combat(self) -> None:
        """End the combat encounter."""
        self.is_active = False


class GameState(BaseModel):
    """Complete game state for a D&D session."""

    # Game identification
    game_id: str = Field(pattern=r"^[a-z0-9-]+$")
    created_at: datetime = Field(default_factory=datetime.now)
    last_saved: datetime = Field(default_factory=datetime.now)

    # Core game data
    character: CharacterSheet
    npcs: list[NPCSheet] = Field(default_factory=list)

    # Scenario information
    scenario_id: str | None = None
    scenario_title: str | None = None
    current_location_id: str | None = None

    # Location and time
    location: str = "Unknown"
    description: str = ""
    game_time: GameTime = Field(default_factory=GameTime)

    # Combat state (optional)
    combat: CombatState | None = None

    # Quest and story tracking
    quest_flags: dict[str, JSONSerializable] = Field(default_factory=dict)
    story_notes: list[str] = Field(default_factory=list)

    # Conversation history (narrative only)
    conversation_history: list[Message] = Field(default_factory=list)

    # Game events (mechanics and tool calls)
    game_events: list[GameEvent] = Field(default_factory=list)

    # Agent tracking for multi-agent support
    active_agent: str = "narrative"

    # Session metadata
    session_number: int = Field(ge=1, default=1)
    total_play_time_minutes: int = Field(ge=0, default=0)

    def add_message(
        self,
        role: MessageRole,
        content: str,
        agent_type: str = "narrative",
        location: str | None = None,
        npcs_mentioned: list[str] | None = None,
        combat_round: int | None = None,
    ) -> None:
        """Add a narrative message to conversation history with metadata."""
        message = Message(
            role=role,
            content=content,
            agent_type=agent_type,
            location=location,
            npcs_mentioned=npcs_mentioned if npcs_mentioned is not None else [],
            combat_round=combat_round,
        )
        self.conversation_history.append(message)

    def add_game_event(
        self,
        event_type: GameEventType,
        tool_name: str | None = None,
        parameters: dict[str, JSONSerializable] | None = None,
        result: JSONSerializable | None = None,
        metadata: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """Add a game mechanics event."""
        event = GameEvent(
            event_type=event_type,
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            metadata=metadata,
        )
        self.game_events.append(event)

    def add_npc(self, npc: NPCSheet) -> None:
        """Add an NPC to the game."""
        # Check for duplicate names and rename if necessary
        existing_names = [n.name for n in self.npcs]
        if npc.name in existing_names:
            counter = 2
            base_name = npc.name
            while f"{base_name} {counter}" in existing_names:
                counter += 1
            npc.name = f"{base_name} {counter}"

        self.npcs.append(npc)

    def remove_npc(self, name: str) -> bool:
        """Remove an NPC by name. Returns True if found and removed."""
        for i, npc in enumerate(self.npcs):
            if npc.name == name:
                del self.npcs[i]
                return True
        return False

    def get_npc(self, name: str) -> NPCSheet | None:
        """Get an NPC by name."""
        for npc in self.npcs:
            if npc.name == name:
                return npc
        return None

    def get_active_npcs(self) -> list[NPCSheet]:
        """Get all NPCs that are still alive."""
        return [npc for npc in self.npcs if npc.is_alive()]

    def start_combat(self) -> CombatState:
        """Initialize combat state."""
        self.combat = CombatState()
        return self.combat

    def end_combat(self) -> None:
        """End current combat encounter."""
        if self.combat:
            self.combat.end_combat()
            # Remove dead NPCs
            self.npcs = [npc for npc in self.npcs if npc.is_alive()]
            self.combat = None

    def set_quest_flag(self, flag_name: str, value: JSONSerializable = True) -> None:
        """Set a quest flag."""
        self.quest_flags[flag_name] = value

    def check_quest_flag(self, flag_name: str) -> bool:
        """Check if a quest flag is set."""
        value = self.quest_flags.get(flag_name, False)
        # Convert to bool for backward compatibility
        return bool(value)

    def add_story_note(self, note: str) -> None:
        """Add a note to the story log."""
        self.story_notes.append(f"[Day {self.game_time.day}] {note}")

    def change_location(self, new_location: str, description: str = "") -> None:
        """Change the current location."""
        self.location = new_location
        self.description = description
        self.add_story_note(f"Moved to {new_location}")

    def get_recent_messages(self, count: int = 10) -> list[Message]:
        """Get the most recent messages from history."""
        return self.conversation_history[-count:] if self.conversation_history else []

    def get_messages_for_agent(self, agent_type: str) -> list[Message]:
        """Get conversation history filtered for a specific agent."""
        return [msg for msg in self.conversation_history if msg.agent_type == agent_type]

    def update_save_time(self) -> None:
        """Update the last saved timestamp."""
        self.last_saved = datetime.now()

    def to_save_dict(self) -> dict[str, Any]:
        """Convert game state to dictionary for saving."""
        return self.model_dump(mode="json")

    @classmethod
    def from_save_dict(cls, data: dict[str, Any]) -> "GameState":
        """Create game state from saved dictionary."""
        return cls(**data)
