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
from app.models.quest import Quest
from app.utils.names import dedupe_display_name


class MessageRole(str, Enum):
    """Message sender role."""

    PLAYER = "player"
    DM = "dm"


class Message(BaseModel):
    """Chat message in game history - narrative only."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_type: AgentType = AgentType.NARRATIVE
    location: str | None = None
    npcs_mentioned: list[str] = Field(default_factory=list)
    combat_round: int | None = None


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

    def to_string(self) -> str:
        """Get human-readable time string."""
        hour_12 = self.hour % 12 if self.hour % 12 != 0 else 12
        am_pm = "AM" if self.hour < 12 else "PM"
        return f"Day {self.day}, {hour_12}:{self.minute:02d} {am_pm}"


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

    # Location and time
    location: str = "Unknown"
    description: str = ""
    game_time: GameTime = Field(default_factory=GameTime)

    # Combat state
    combat: CombatState = Field(default_factory=CombatState)

    # Story tracking
    story_notes: list[str] = Field(default_factory=list)

    # Conversation history (narrative only)
    conversation_history: list[Message] = Field(default_factory=list)

    # Game events (mechanics and tool calls)
    game_events: list[GameEvent] = Field(default_factory=list)

    # Agent tracking for multi-agent support
    active_agent: AgentType = AgentType.NARRATIVE

    # Session metadata
    session_number: int = Field(ge=1, default=1)
    total_play_time_minutes: int = Field(ge=0, default=0)

    def add_message(self, message: Message) -> None:
        """Add a message to conversation history with metadata."""
        self.conversation_history.append(message)

    def add_game_event(self, event: GameEvent) -> None:
        """Add a game mechanics event."""
        self.game_events.append(event)

    def add_npc(self, npc: NPCInstance) -> None:
        """Add an NPC to the game."""
        # Check for duplicate names and rename if necessary
        existing_names = [n.sheet.character.name for n in self.npcs]
        if npc.sheet.character.name in existing_names:
            counter = 2
            base_name = npc.sheet.character.name
            while f"{base_name} {counter}" in existing_names:
                counter += 1
            npc.sheet.character.name = f"{base_name} {counter}"
        self.npcs.append(npc)

    def remove_npc(self, name: str) -> bool:
        """Remove an NPC by name. Returns True if found and removed."""
        for i, npc in enumerate(self.npcs):
            if npc.sheet.character.name == name:
                del self.npcs[i]
                return True
        return False

    def add_monster_instance(self, monster: MonsterInstance) -> str:
        """Add a MonsterInstance to the game and ensure unique display name.

        Returns final display name (with suffix if deduped). Mutates the instance's
        sheet.name if deduping is applied to maintain display consistency across systems.
        """
        existing_names = [m.sheet.name for m in self.monsters]
        final_name = dedupe_display_name(existing_names, monster.sheet.name)
        monster.sheet.name = final_name

        self.monsters.append(monster)
        return final_name

    def remove_monster(self, name: str) -> bool:
        for i, m in enumerate(self.monsters):
            if m.sheet.name == name:
                del self.monsters[i]
                return True
        return False

    def get_monster(self, name: str) -> MonsterInstance | None:
        for m in self.monsters:
            if m.sheet.name == name:
                return m
        return None

    def get_active_monsters(self) -> list[MonsterInstance]:
        return [m for m in self.monsters if m.is_alive()]

    def get_npc(self, name: str) -> NPCInstance | None:
        """Get an NPC by name."""
        for npc in self.npcs:
            if npc.sheet.character.name == name:
                return npc
        return None

    def get_active_npcs(self) -> list[NPCInstance]:
        """Get all NPCs that are still alive."""
        return [npc for npc in self.npcs if npc.is_alive()]

    def get_npcs_at_location(self, location_id: str) -> list[NPCInstance]:
        """Get all NPCs currently at the specified location."""
        return [npc for npc in self.npcs if npc.current_location_id == location_id]

    def find_entity_by_name(self, name: str) -> tuple[EntityType, IEntity] | None:
        """Find any entity by display name (case-insensitive)."""
        # Player
        if self.character.sheet.name.lower() == name.lower():
            return (EntityType.PLAYER, self.character)

        # NPCs
        for npc in self.npcs:
            if npc.sheet.character.name.lower() == name.lower():
                return (EntityType.NPC, npc)

        # Monsters
        for mon in self.monsters:
            if mon.sheet.name.lower() == name.lower():
                return (EntityType.MONSTER, mon)

        return None

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

    def move_npc(self, npc_id: str, to_location_id: str) -> NPCInstance:
        """Move an NPC to a different location.

        Args:
            npc_id: The NPC instance ID to move
            to_location_id: The target location ID

        Returns:
            The moved NPC instance

        Raises:
            ValueError: If NPC not found
        """
        npc = self.get_npc_by_id(npc_id)
        if not npc:
            raise ValueError(f"NPC with id '{npc_id}' not found")

        npc.current_location_id = to_location_id
        npc.touch()
        return npc

    def start_combat(self) -> CombatState:
        """Initialize combat state."""
        self.combat = CombatState(is_active=True)
        return self.combat

    def end_combat(self) -> None:
        """End current combat encounter."""
        if self.combat.is_active:
            self.combat.end_combat()
            # Remove dead monsters
            self.monsters = [m for m in self.monsters if m.is_alive()]
            # Set combat to inactive and clear participants
            self.combat.is_active = False
            self.combat.participants.clear()
            self.combat.round_number = 1
            self.combat.turn_index = 0

    def set_quest_flag(self, flag_name: str, value: JSONSerializable = True) -> None:
        """Set a quest flag."""
        self.scenario_instance.quest_flags[flag_name] = value

    def check_quest_flag(self, flag_name: str) -> bool:
        """Check if a quest flag is set."""
        value = self.scenario_instance.quest_flags.get(flag_name, False)
        return bool(value)

    def add_story_note(self, note: str) -> None:
        """Add a note to the story log."""
        self.story_notes.append(f"[Day {self.game_time.day}] {note}")

    def change_location(self, new_location_id: str, new_location_name: str, description: str = "") -> None:
        """Change the current location."""
        # Update location state tracking within scenario instance
        if new_location_id not in self.scenario_instance.location_states:
            self.scenario_instance.location_states[new_location_id] = LocationState(location_id=new_location_id)
        location_state = self.scenario_instance.location_states[new_location_id]
        location_state.mark_visited()
        self.scenario_instance.current_location_id = new_location_id

        self.location = new_location_name
        self.description = description
        self.add_story_note(f"Moved to {new_location_name}")

    def get_messages_for_agent(self, agent_type: AgentType) -> list[Message]:
        """Get conversation history filtered for a specific agent."""
        return [msg for msg in self.conversation_history if msg.agent_type == agent_type]

    def update_save_time(self) -> None:
        """Update the last saved timestamp."""
        self.last_saved = datetime.now()

    def get_location_state(self, location_id: str) -> LocationState:
        """Get or create location state from scenario_instance."""
        if location_id not in self.scenario_instance.location_states:
            self.scenario_instance.location_states[location_id] = LocationState(location_id=location_id)
        return self.scenario_instance.location_states[location_id]

    def add_quest(self, quest: Quest) -> None:
        """Add a quest to active quests."""
        for q in self.scenario_instance.active_quests:
            if q.id == quest.id:
                return
        self.scenario_instance.active_quests.append(quest)
        self.add_story_note(f"New quest started: {quest.name}")

    def complete_quest(self, quest_id: str) -> bool:
        """Mark a quest as completed. Returns True if found."""
        for i, quest in enumerate(self.scenario_instance.active_quests):
            if quest.id == quest_id:
                self.scenario_instance.active_quests.pop(i)
                self.scenario_instance.completed_quest_ids.append(quest_id)
                self.add_story_note(f"Quest completed: {quest.name}")
                return True
        return False

    def get_active_quest(self, quest_id: str) -> Quest | None:
        """Get an active quest by ID."""
        for quest in self.scenario_instance.active_quests:
            if quest.id == quest_id:
                return quest
        return None
