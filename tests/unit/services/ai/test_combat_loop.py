"""Unit tests for combat_loop ally suggestion generation."""

from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant, CombatState


class TestCombatParticipantFactions:
    """Test that combat participants can be properly categorized by faction."""

    def test_ally_faction_detection(self) -> None:
        """Test that ALLY faction is properly set and detected."""
        ally = CombatParticipant(
            entity_id="npc-ally-1",
            entity_type=EntityType.NPC,
            faction=CombatFaction.ALLY,
            name="Eldrin the Wise",
            initiative=14,
            is_player=False,
            is_active=True,
        )

        assert ally.faction == CombatFaction.ALLY
        assert not ally.is_player
        assert ally.entity_type == EntityType.NPC

    def test_enemy_faction_detection(self) -> None:
        """Test that ENEMY faction is properly set and detected."""
        enemy = CombatParticipant(
            entity_id="monster-1",
            entity_type=EntityType.MONSTER,
            faction=CombatFaction.ENEMY,
            name="Goblin",
            initiative=12,
            is_player=False,
            is_active=True,
        )

        assert enemy.faction == CombatFaction.ENEMY
        assert enemy.entity_type == EntityType.MONSTER

    def test_player_faction_detection(self) -> None:
        """Test that PLAYER faction is properly set and detected."""
        player = CombatParticipant(
            entity_id="player",
            entity_type=EntityType.PLAYER,
            faction=CombatFaction.PLAYER,
            name="Aldric",
            initiative=15,
            is_player=True,
            is_active=True,
        )

        assert player.faction == CombatFaction.PLAYER
        assert player.is_player
        assert player.entity_type == EntityType.PLAYER


class TestCombatStateCurrentTurn:
    """Test combat state's current turn detection."""

    def test_get_current_turn_with_ally(self) -> None:
        """Test getting current turn when it's an ally's turn."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=1,  # Second participant (ally)
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                ),
                CombatParticipant(
                    entity_id="monster-1",
                    entity_type=EntityType.MONSTER,
                    faction=CombatFaction.ENEMY,
                    name="Goblin",
                    initiative=12,
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.faction == CombatFaction.ALLY
        assert current.entity_id == "npc-ally-1"
        assert current.entity_type == EntityType.NPC

    def test_get_current_turn_with_enemy(self) -> None:
        """Test getting current turn when it's an enemy's turn."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=2,  # Third participant (enemy)
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                ),
                CombatParticipant(
                    entity_id="monster-1",
                    entity_type=EntityType.MONSTER,
                    faction=CombatFaction.ENEMY,
                    name="Goblin",
                    initiative=12,
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.faction == CombatFaction.ENEMY
        assert current.entity_id == "monster-1"

    def test_get_current_turn_skips_inactive(self) -> None:
        """Test that inactive participants are skipped."""
        combat = CombatState(
            is_active=True,
            round_number=1,
            turn_index=0,  # First active participant
            participants=[
                CombatParticipant(
                    entity_id="player",
                    entity_type=EntityType.PLAYER,
                    faction=CombatFaction.PLAYER,
                    name="Aldric",
                    initiative=15,
                    is_player=True,
                    is_active=False,  # Inactive
                ),
                CombatParticipant(
                    entity_id="npc-ally-1",
                    entity_type=EntityType.NPC,
                    faction=CombatFaction.ALLY,
                    name="Eldrin",
                    initiative=14,
                    is_active=True,  # Active
                ),
            ],
        )

        current = combat.get_current_turn()
        assert current is not None
        assert current.entity_id == "npc-ally-1"
        assert current.is_active
