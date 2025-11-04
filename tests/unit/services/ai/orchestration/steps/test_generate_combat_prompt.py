"""Tests for GenerateCombatPrompt step."""

from unittest.mock import create_autospec

import pytest

from app.interfaces.services.game import ICombatService
from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext, OrchestrationFlags
from app.services.ai.orchestration.steps.generate_combat_prompt import GenerateCombatPrompt
from tests.factories import make_combat_participant, make_combat_state, make_game_state


class TestGenerateCombatPrompt:
    """Tests for GenerateCombatPrompt step."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.game_state = make_game_state(game_id="test-game")
        self.combat_service = create_autospec(ICombatService, instance=True)
        self.step = GenerateCombatPrompt(self.combat_service)

    @pytest.mark.asyncio
    async def test_reads_tracking_from_flags(self) -> None:
        """Test that step reads last_prompted_entity_id and last_prompted_round from flags."""
        combat_state = make_combat_state(is_active=True, round_number=3)
        goblin = make_combat_participant(
            entity_id="goblin-1",
            entity_type=EntityType.MONSTER,
            name="Goblin",
            initiative=15,
            faction=CombatFaction.ENEMY,
        )
        combat_state.participants = [goblin]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state

        self.combat_service.generate_combat_prompt.return_value = "Goblin's turn!"

        flags = OrchestrationFlags(
            last_prompted_entity_id="player-1",
            last_prompted_round=2,
        )
        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
            flags=flags,
        )

        await self.step.run(ctx)

        # Verify combat service was called with tracking params
        self.combat_service.generate_combat_prompt.assert_called_once_with(
            self.game_state,
            last_entity_id="player-1",
            last_round=2,
        )

    @pytest.mark.asyncio
    async def test_updates_flags_with_current_entity_and_round(self) -> None:
        """Test that step updates flags with current entity_id and round."""
        combat_state = make_combat_state(is_active=True, round_number=7)
        goblin = make_combat_participant(
            entity_id="goblin-123",
            entity_type=EntityType.MONSTER,
            name="Goblin",
            initiative=15,
            faction=CombatFaction.ENEMY,
        )
        combat_state.participants = [goblin]
        combat_state.turn_index = 0
        self.game_state.combat = combat_state

        self.combat_service.generate_combat_prompt.return_value = "Goblin attacks!"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        # Verify flags updated
        assert result.context.flags.last_prompted_entity_id == "goblin-123"
        assert result.context.flags.last_prompted_round == 7

    @pytest.mark.asyncio
    async def test_stores_prompt_in_current_prompt(self) -> None:
        """Test that step stores prompt in ctx.current_prompt."""
        combat_state = make_combat_state(is_active=True)
        self.game_state.combat = combat_state

        self.combat_service.generate_combat_prompt.return_value = "Enemy's turn to act!"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        assert result.context.current_prompt == "Enemy's turn to act!"

    @pytest.mark.asyncio
    async def test_handles_no_current_turn(self) -> None:
        """Test that step handles case when no current turn exists."""
        combat_state = make_combat_state(is_active=True)
        combat_state.participants = []  # No participants
        self.game_state.combat = combat_state

        self.combat_service.generate_combat_prompt.return_value = "No active turn"

        ctx = OrchestrationContext(
            user_message="Continue",
            game_state=self.game_state,
        )

        result = await self.step.run(ctx)

        # Should handle gracefully
        assert result.context.flags.last_prompted_entity_id is None
        assert result.context.current_prompt == "No active turn"
