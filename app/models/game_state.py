"""Game state models for D&D 5e game session management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.models.attributes import EntityType
from app.models.combat import CombatState
from app.models.entity import IEntity
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.instances.scenario_instance import ScenarioInstance
from app.models.location import LocationState
from app.models.party import PartyState
from app.models.player_journal import PlayerJournalEntry


class MessageRole(str, Enum):
    """Message sender role."""

    PLAYER = "player"
    DM = "dm"
    NPC = "npc"


class Message(BaseModel):
    """Chat message in game history (player, DM, or NPC)."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_type: AgentType = AgentType.NARRATIVE
    location: str | None = None
    npcs_mentioned: list[str] = Field(default_factory=list)
    combat_round: int | None = None
    combat_occurrence: int | None = None
    speaker_npc_id: str | None = None
    speaker_npc_name: str | None = None


class GameEventType(str, Enum):
    """Types of game events."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class GameEvent(BaseModel):
    """Game mechanics event that update the GameState."""

    event_type: GameEventType
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_name: str
    parameters: dict[str, JSONSerializable] = Field(default_factory=dict)
    result: dict[str, JSONSerializable] = Field(default_factory=dict)


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


class DialogueSessionMode(str, Enum):
    """Supported dialogue session modes."""

    EXPLICIT_ONLY = "explicit_only"
    STICKY = "sticky"


class DialogueSessionState(BaseModel):
    """Tracks state for ongoing NPC dialogue sessions."""

    active: bool = False
    target_npc_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    last_interaction_at: datetime | None = None
    mode: DialogueSessionMode = DialogueSessionMode.EXPLICIT_ONLY


class GameState(BaseModel):
    """Complete game state for a D&D session."""

    # Game identification
    game_id: str = Field(pattern=r"^[a-z0-9-]+$")
    created_at: datetime = Field(default_factory=datetime.now)
    last_saved: datetime = Field(default_factory=datetime.now)

    # Core game data (instances)
    character: CharacterInstance
    npcs: list[NPCInstance] = Field(default_factory=list)
    monsters: list[MonsterInstance] = Field(default_factory=list)

    # Scenario information
    scenario_id: str
    scenario_title: str
    scenario_instance: ScenarioInstance

    # Content packs for this game session (scenario + user selections)
    content_packs: list[str] = Field(default_factory=lambda: ["srd"])

    # Location and time
    location: str = "Unknown"
    description: str = ""
    game_time: GameTime = Field(default_factory=GameTime)

    # Combat state
    combat: CombatState = Field(default_factory=CombatState)

    # Party state
    party: PartyState = Field(default_factory=PartyState)

    # Story tracking
    story_notes: list[str] = Field(default_factory=list)

    # Player journal entries (user-editable notes)
    player_journal_entries: list[PlayerJournalEntry] = Field(default_factory=list)

    # Conversation history (player/DM/NPC dialogue)
    conversation_history: list[Message] = Field(default_factory=list)

    # Game events (mechanics and tool calls)
    game_events: list[GameEvent] = Field(default_factory=list)

    # Dialogue session tracking
    dialogue_session: DialogueSessionState = Field(default_factory=DialogueSessionState)

    # Agent tracking for multi-agent support
    active_agent: AgentType = AgentType.NARRATIVE

    # Session metadata
    session_number: int = Field(ge=1, default=1)
    total_play_time_minutes: int = Field(ge=0, default=0)

    def get_entity_by_id(self, entity_type: EntityType, entity_id: str) -> IEntity | None:
        """Resolve an entity by type and instance id for all operations (combat, HP, conditions, etc)."""
        match entity_type:
            case EntityType.PLAYER:
                if self.character.instance_id == entity_id:
                    return self.character
            case EntityType.NPC:
                for npc in self.npcs:
                    if npc.instance_id == entity_id:
                        return npc
            case EntityType.MONSTER:
                for mon in self.monsters:
                    if mon.instance_id == entity_id:
                        return mon
        return None  # Entity with given ID not found

    def get_npc_by_id(self, npc_id: str) -> NPCInstance | None:
        """Resolve an NPC instance by id (location/state aware)."""
        for npc in self.npcs:
            if npc.instance_id == npc_id:
                return npc
        return None

    def get_npc_by_scenario_id(self, scenario_npc_id: str) -> NPCInstance | None:
        """Resolve an NPC instance by its scenario NPC ID.

        Useful when encounters reference scenario-defined NPC IDs rather than instance IDs.
        """
        for npc in self.npcs:
            if npc.scenario_npc_id == scenario_npc_id:
                return npc
        return None

    def add_story_note(self, note: str) -> None:
        """Add a note to the story log."""
        self.story_notes.append(f"[Day {self.game_time.day}] {note}")

    def get_messages_for_agent(self, agent_type: AgentType) -> list[Message]:
        """Get conversation history filtered for a specific agent."""
        return [msg for msg in self.conversation_history if msg.agent_type == agent_type]

    def get_messages_for_combat(self, occurrence: int) -> list[Message]:
        """Get conversation history for a specific combat occurrence."""
        return [msg for msg in self.conversation_history if msg.combat_occurrence == occurrence]

    def update_save_time(self) -> None:
        """Update the last saved timestamp."""
        self.last_saved = datetime.now()

    def get_location_state(self, location_id: str) -> LocationState:
        """Get or create location state from scenario_instance."""
        if location_id not in self.scenario_instance.location_states:
            self.scenario_instance.location_states[location_id] = LocationState(location_id=location_id)
        return self.scenario_instance.location_states[location_id]

    def add_journal_entry(self, entry: PlayerJournalEntry) -> None:
        """Add a new journal entry to the player's journal.

        Args:
            entry: The journal entry to add
        """
        self.player_journal_entries.append(entry)

    def get_journal_entry(self, entry_id: str) -> PlayerJournalEntry | None:
        """Get a journal entry by its ID.

        Args:
            entry_id: The entry ID to look up

        Returns:
            The journal entry if found, None otherwise
        """
        for entry in self.player_journal_entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def update_journal_entry(
        self, entry_id: str, content: str, tags: list[str], pinned: bool
    ) -> PlayerJournalEntry | None:
        """Update an existing journal entry's content, tags, and pinned status.

        Args:
            entry_id: The entry ID to update
            content: New content for the entry
            tags: New tags for the entry
            pinned: New pinned status for the entry

        Returns:
            The updated journal entry if found, None otherwise
        """
        entry = self.get_journal_entry(entry_id)
        if entry is None:
            return None

        entry.content = content
        entry.tags = tags
        entry.pinned = pinned
        entry.touch()
        return entry

    def delete_journal_entry(self, entry_id: str) -> bool:
        """Delete a journal entry by its ID.

        Args:
            entry_id: The entry ID to delete

        Returns:
            True if the entry was found and deleted, False otherwise
        """
        for i, entry in enumerate(self.player_journal_entries):
            if entry.entry_id == entry_id:
                self.player_journal_entries.pop(i)
                return True
        return False
