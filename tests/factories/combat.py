"""Combat state factory helpers for testing."""

from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant, CombatState


def make_combat_state(
    *,
    is_active: bool = False,
    round_number: int = 1,
    turn_index: int = 0,
    participants: list[CombatParticipant] | None = None,
    combat_occurrence: int = 1,
) -> CombatState:
    """Create a CombatState for testing.

    Args:
        is_active: Whether combat is currently active
        round_number: Current round number
        turn_index: Index of current turn in participants list
        participants: List of combat participants (defaults to empty)
        combat_occurrence: Unique combat occurrence number

    Returns:
        Configured CombatState instance
    """
    return CombatState(
        is_active=is_active,
        round_number=round_number,
        turn_index=turn_index,
        participants=participants or [],
        combat_occurrence=combat_occurrence,
    )


def make_combat_participant(
    *,
    entity_id: str = "test-entity-1",
    entity_type: EntityType = EntityType.MONSTER,
    name: str = "Test Entity",
    initiative: int = 10,
    faction: CombatFaction = CombatFaction.ENEMY,
) -> CombatParticipant:
    """Create a CombatParticipant for testing.

    Args:
        entity_id: Unique entity ID
        entity_type: Type of entity (PLAYER, NPC, MONSTER)
        name: Display name
        initiative: Initiative roll value
        faction: Combat faction (PLAYER, ALLY, ENEMY, NEUTRAL)

    Returns:
        Configured CombatParticipant instance
    """
    return CombatParticipant(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        initiative=initiative,
        faction=faction,
    )
