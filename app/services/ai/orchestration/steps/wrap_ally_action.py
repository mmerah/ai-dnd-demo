"""Step to wrap user messages for allied NPC combat turns."""

import logging

from app.models.attributes import EntityType
from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext
from app.services.ai.orchestration.step import StepResult

logger = logging.getLogger(__name__)


class WrapAllyActionIfNeeded:
    """Rewrite user message when it's an allied NPC's combat turn.

    This step detects if the current turn belongs to an allied NPC and rewrites
    the user message to instruct the combat agent to execute the action properly,
    including calling next_turn.

    The rewrite only happens if:
    1. Combat is active
    2. Current turn belongs to an ALLY faction
    3. Entity is an NPC
    4. Message doesn't already start with [ALLY_ACTION]
    5. NPC exists in game state and is in the party
    """

    async def run(self, ctx: OrchestrationContext) -> StepResult:
        """Check if ally action wrapping is needed and rewrite message if so.

        Args:
            ctx: Current orchestration context

        Returns:
            StepResult with potentially updated user_message

        Raises:
            ValueError: If ally NPC not found or not in party
        """
        # Only apply during combat
        if not ctx.game_state.combat.is_active:
            return StepResult.continue_with(ctx)

        # Check if already wrapped
        if ctx.user_message.lstrip().startswith("[ALLY_ACTION]"):
            return StepResult.continue_with(ctx)

        # Get current turn info
        current_turn = ctx.game_state.combat.get_current_turn()
        if not current_turn:
            return StepResult.continue_with(ctx)

        # Check if it's an ally NPC turn
        if current_turn.faction != CombatFaction.ALLY or current_turn.entity_type != EntityType.NPC:
            return StepResult.continue_with(ctx)

        # Validate NPC exists
        npc = ctx.game_state.get_npc_by_id(current_turn.entity_id)
        if npc is None:
            raise ValueError(f"Allied NPC {current_turn.entity_id} not found in game state during combat turn")

        # Validate NPC is in party
        if not ctx.game_state.party.has_member(npc.instance_id):
            raise ValueError(
                f"NPC {npc.display_name} ({npc.instance_id}) has ALLY faction in combat " f"but is not in the party"
            )

        # Rewrite message (orchestrator lines 101-105)
        wrapped_message = (
            f"[ALLY_ACTION] It is {npc.display_name}'s turn in combat (entity_id={npc.instance_id}, allied NPC). "
            f"Execute this action exactly as described: {ctx.user_message}. "
            "Use the appropriate combat tools (rolls, damage, HP updates) and CALL next_turn immediately once resolved."
        )

        logger.debug(
            "Wrapped ally action for %s (entity_id=%s)",
            npc.display_name,
            npc.instance_id,
        )

        # Update context with wrapped message
        updated_ctx = ctx.with_updates(user_message=wrapped_message)

        return StepResult.continue_with(updated_ctx)
