"""Tests for orchestration guard predicates."""

from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.guards import (
    combat_just_ended,
    combat_just_started,
    combat_loop_should_continue,
    has_npc_targets,
    is_current_turn_ally,
    is_current_turn_npc_or_monster,
    is_player_turn,
    no_enemies_remaining,
)
from tests.factories import make_combat_participant, make_game_state


class TestCombatJustStarted:
    """Tests for combat_just_started guard."""

    def test_returns_true_when_combat_just_started(self) -> None:
        """Test guard returns True when combat transitioned from inactive to active."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        flags = OrchestrationFlags(combat_was_active=False)
        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state, flags=flags)

        assert combat_just_started(ctx) is True

    def test_returns_false_when_combat_was_already_active(self) -> None:
        """Test guard returns False when combat was already active."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        flags = OrchestrationFlags(combat_was_active=True)
        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state, flags=flags)

        assert combat_just_started(ctx) is False

    def test_returns_false_when_combat_not_active(self) -> None:
        """Test guard returns False when combat is not active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        flags = OrchestrationFlags(combat_was_active=False)
        ctx = OrchestrationContext(user_message="Hello", game_state=game_state, flags=flags)

        assert combat_just_started(ctx) is False

    def test_returns_false_when_combat_ended(self) -> None:
        """Test guard returns False when combat just ended."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        flags = OrchestrationFlags(combat_was_active=True)
        ctx = OrchestrationContext(user_message="Victory!", game_state=game_state, flags=flags)

        assert combat_just_started(ctx) is False


class TestCombatJustEnded:
    """Tests for combat_just_ended guard."""

    def test_returns_true_when_combat_just_ended(self) -> None:
        """Test guard returns True when combat transitioned from active to inactive."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        flags = OrchestrationFlags(combat_was_active=True)
        ctx = OrchestrationContext(user_message="Victory!", game_state=game_state, flags=flags)

        assert combat_just_ended(ctx) is True

    def test_returns_false_when_combat_still_active(self) -> None:
        """Test guard returns False when combat is still active."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        flags = OrchestrationFlags(combat_was_active=True)
        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state, flags=flags)

        assert combat_just_ended(ctx) is False

    def test_returns_false_when_combat_was_never_active(self) -> None:
        """Test guard returns False when combat was never active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        flags = OrchestrationFlags(combat_was_active=False)
        ctx = OrchestrationContext(user_message="Hello", game_state=game_state, flags=flags)

        assert combat_just_ended(ctx) is False

    def test_returns_false_when_combat_just_started(self) -> None:
        """Test guard returns False when combat just started."""
        game_state = make_game_state()
        game_state.combat.is_active = True

        flags = OrchestrationFlags(combat_was_active=False)
        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state, flags=flags)

        assert combat_just_ended(ctx) is False


class TestHasNpcTargets:
    """Tests for has_npc_targets guard."""

    def test_returns_true_when_npcs_targeted(self) -> None:
        """Test guard returns True when NPC targets exist."""
        game_state = make_game_state()

        flags = OrchestrationFlags(npc_targets=["npc1", "npc2"])
        ctx = OrchestrationContext(user_message="@npc1 hello", game_state=game_state, flags=flags)

        assert has_npc_targets(ctx) is True

    def test_returns_false_when_no_npcs_targeted(self) -> None:
        """Test guard returns False when no NPC targets."""
        game_state = make_game_state()

        flags = OrchestrationFlags(npc_targets=[])
        ctx = OrchestrationContext(user_message="Hello", game_state=game_state, flags=flags)

        assert has_npc_targets(ctx) is False

    def test_returns_false_when_npc_targets_is_empty_list(self) -> None:
        """Test guard returns False with explicit empty list."""
        game_state = make_game_state()

        flags = OrchestrationFlags(npc_targets=[])
        ctx = OrchestrationContext(user_message="Hello", game_state=game_state, flags=flags)

        assert has_npc_targets(ctx) is False


class TestNoEnemiesRemaining:
    """Tests for no_enemies_remaining guard (Phase 5.5)."""

    def test_returns_true_when_no_enemies(self) -> None:
        """Test guard returns True when no active enemies remain."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        game_state.combat.participants = [
            make_combat_participant(faction=CombatFaction.PLAYER),
            make_combat_participant(faction=CombatFaction.ALLY),
        ]

        ctx = OrchestrationContext(user_message="Victory!", game_state=game_state)
        assert no_enemies_remaining(ctx) is True

    def test_returns_false_when_enemies_remain(self) -> None:
        """Test guard returns False when active enemies exist."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        game_state.combat.participants = [
            make_combat_participant(faction=CombatFaction.PLAYER),
            make_combat_participant(faction=CombatFaction.ENEMY),
        ]

        ctx = OrchestrationContext(user_message="Fight!", game_state=game_state)
        assert no_enemies_remaining(ctx) is False

    def test_returns_false_when_combat_not_active(self) -> None:
        """Test guard returns False when combat is not active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        ctx = OrchestrationContext(user_message="Hello", game_state=game_state)
        assert no_enemies_remaining(ctx) is False

    def test_returns_true_when_enemies_inactive(self) -> None:
        """Test guard returns True when enemies exist but are inactive."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        defeated_enemy = make_combat_participant(faction=CombatFaction.ENEMY)
        defeated_enemy.is_active = False
        game_state.combat.participants = [
            make_combat_participant(faction=CombatFaction.PLAYER),
            defeated_enemy,
        ]

        ctx = OrchestrationContext(user_message="Victory!", game_state=game_state)
        assert no_enemies_remaining(ctx) is True


class TestIsCurrentTurnAlly:
    """Tests for is_current_turn_ally guard."""

    def test_returns_true_when_ally_turn(self) -> None:
        """Test guard returns True when current turn is ALLY faction."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        ally = make_combat_participant(faction=CombatFaction.ALLY, initiative=20)
        game_state.combat.participants = [ally]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Act!", game_state=game_state)
        assert is_current_turn_ally(ctx) is True

    def test_returns_false_when_enemy_turn(self) -> None:
        """Test guard returns False when current turn is ENEMY faction."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        enemy = make_combat_participant(faction=CombatFaction.ENEMY, initiative=20)
        game_state.combat.participants = [enemy]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=game_state)
        assert is_current_turn_ally(ctx) is False

    def test_returns_false_when_combat_not_active(self) -> None:
        """Test guard returns False when combat is not active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        ctx = OrchestrationContext(user_message="Hello", game_state=game_state)
        assert is_current_turn_ally(ctx) is False

    def test_returns_false_when_no_current_turn(self) -> None:
        """Test guard returns False when no current turn exists."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        game_state.combat.participants = []

        ctx = OrchestrationContext(user_message="Wait", game_state=game_state)
        assert is_current_turn_ally(ctx) is False


class TestIsCurrentTurnNpcOrMonster:
    """Tests for is_current_turn_npc_or_monster guard (Phase 5.5)."""

    def test_returns_true_for_enemy_turn(self) -> None:
        """Test guard returns True for ENEMY faction turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        enemy = make_combat_participant(faction=CombatFaction.ENEMY, initiative=20)
        game_state.combat.participants = [enemy]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=game_state)
        assert is_current_turn_npc_or_monster(ctx) is True

    def test_returns_true_for_neutral_turn(self) -> None:
        """Test guard returns True for NEUTRAL faction turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        neutral = make_combat_participant(faction=CombatFaction.NEUTRAL, initiative=20)
        game_state.combat.participants = [neutral]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Wait", game_state=game_state)
        assert is_current_turn_npc_or_monster(ctx) is True

    def test_returns_false_for_player_turn(self) -> None:
        """Test guard returns False for PLAYER faction turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        player = make_combat_participant(faction=CombatFaction.PLAYER, initiative=20)
        game_state.combat.participants = [player]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state)
        assert is_current_turn_npc_or_monster(ctx) is False

    def test_returns_false_for_ally_turn(self) -> None:
        """Test guard returns False for ALLY faction turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        ally = make_combat_participant(faction=CombatFaction.ALLY, initiative=20)
        game_state.combat.participants = [ally]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Help!", game_state=game_state)
        assert is_current_turn_npc_or_monster(ctx) is False


class TestCombatLoopShouldContinue:
    """Tests for combat_loop_should_continue guard (Phase 5.5)."""

    def test_returns_true_for_enemy_turn(self) -> None:
        """Test guard returns True when it's an enemy turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        enemy = make_combat_participant(faction=CombatFaction.ENEMY, initiative=20)
        game_state.combat.participants = [enemy]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=game_state)
        assert combat_loop_should_continue(ctx) is True

    def test_returns_false_for_player_turn(self) -> None:
        """Test guard returns False when it's the player's turn."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        player = make_combat_participant(faction=CombatFaction.PLAYER, initiative=20)
        game_state.combat.participants = [player]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state)
        assert combat_loop_should_continue(ctx) is False

    def test_returns_false_when_combat_not_active(self) -> None:
        """Test guard returns False when combat is not active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        ctx = OrchestrationContext(user_message="Hello", game_state=game_state)
        assert combat_loop_should_continue(ctx) is False

    def test_returns_false_when_no_current_turn(self) -> None:
        """Test guard returns False when no current turn exists."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        game_state.combat.participants = []

        ctx = OrchestrationContext(user_message="Wait", game_state=game_state)
        assert combat_loop_should_continue(ctx) is False


class TestIsPlayerTurn:
    """Tests for is_player_turn guard (Phase 5.6)."""

    def test_returns_true_when_player_turn(self) -> None:
        """Test guard returns True when current turn is the player."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        player = make_combat_participant(faction=CombatFaction.PLAYER, initiative=20)
        # Mark as player
        player.is_player = True
        game_state.combat.participants = [player]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Attack!", game_state=game_state)
        assert is_player_turn(ctx) is True

    def test_returns_false_when_not_player_turn(self) -> None:
        """Test guard returns False when current turn is not the player."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        enemy = make_combat_participant(faction=CombatFaction.ENEMY, initiative=20)
        game_state.combat.participants = [enemy]
        game_state.combat.turn_index = 0

        ctx = OrchestrationContext(user_message="Fight!", game_state=game_state)
        assert is_player_turn(ctx) is False

    def test_returns_false_when_combat_not_active(self) -> None:
        """Test guard returns False when combat is not active."""
        game_state = make_game_state()
        game_state.combat.is_active = False

        ctx = OrchestrationContext(user_message="Hello", game_state=game_state)
        assert is_player_turn(ctx) is False

    def test_returns_false_when_no_current_turn(self) -> None:
        """Test guard returns False when no current turn exists."""
        game_state = make_game_state()
        game_state.combat.is_active = True
        game_state.combat.participants = []

        ctx = OrchestrationContext(user_message="Wait", game_state=game_state)
        assert is_player_turn(ctx) is False
