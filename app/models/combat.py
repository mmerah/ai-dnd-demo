"""Combat-related models for D&D 5e."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.attributes import EntityType
from app.models.entity import IEntity


class CombatFaction(str, Enum):
    """Faction for combat participants."""

    PLAYER = "player"
    ALLY = "ally"
    ENEMY = "enemy"
    NEUTRAL = "neutral"


class CombatParticipant(BaseModel):
    """Participant in combat with initiative and stable entity reference."""

    # Stable reference to an entity in GameState
    entity_id: str
    entity_type: EntityType
    faction: CombatFaction

    # Display information
    name: str
    initiative: int | None = None
    is_player: bool = False
    is_active: bool = True


class CombatState(BaseModel):
    """Combat encounter state."""

    round_number: int = Field(ge=1, default=1)
    turn_index: int = Field(ge=0, default=0)
    participants: list[CombatParticipant] = Field(default_factory=list)
    is_active: bool = False
    combat_occurrence: int = Field(ge=0, default=0)

    def add_participant(
        self,
        name: str,
        initiative: int,
        is_player: bool = False,
        *,
        entity_id: str,
        entity_type: EntityType,
        faction: CombatFaction,
    ) -> None:
        """Add a participant to combat (id-aware)."""
        participant = CombatParticipant(
            name=name,
            initiative=initiative,
            is_player=is_player,
            entity_id=entity_id,
            entity_type=entity_type,
            faction=faction,
        )
        self.participants.append(participant)
        self.sort_by_initiative()

    def sort_by_initiative(self) -> None:
        """Sort participants by initiative (highest first)."""
        # Only sort participants that have initiative set
        self.participants.sort(key=lambda p: p.initiative if p.initiative is not None else -1, reverse=True)

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

    def remove_participant_by_id(self, entity_id: str) -> None:
        """Remove a participant by entity instance ID."""
        self.participants = [p for p in self.participants if p.entity_id != entity_id]
        active_participants = [p for p in self.participants if p.is_active]
        if self.turn_index >= len(active_participants):
            self.turn_index = 0

    def end_combat(self) -> None:
        """End the combat encounter."""
        self.is_active = False

    def get_turn_order_display(self) -> str:
        """Return a formatted turn order display string."""
        if not self.participants:
            return "No participants in combat"
        current = self.get_current_turn()
        current_id = current.entity_id if current else None
        lines = [f"Round {self.round_number} - Turn Order:"]
        turn_num = 1
        for p in self.participants:
            if not p.is_active:
                continue
            marker = "→ " if current_id and p.entity_id == current_id else "  "
            tag = " [PLAYER]" if p.is_player else ""
            init = p.initiative if p.initiative is not None else 0
            lines.append(f"{marker}{turn_num}. {p.name}{tag} (Initiative: {init}, ID: {p.entity_id})")
            turn_num += 1
        return "\n".join(lines)


class MonsterSpawnInfo(BaseModel):
    """Information for spawning monsters from the database."""

    monster_index: str
    quantity: int = Field(default=1, ge=1)


class CombatEntry(BaseModel):
    """Entity-faction pairing for combat initialization.

    Used as an intermediate type when adding entities to combat.
    The faction can be explicitly specified or inferred if None.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entity: IEntity
    faction: CombatFaction | None = None
