"""Guard predicates for conditional pipeline execution.

Guards are pure predicate functions that inspect OrchestrationContext and
return a boolean to determine whether conditional steps should execute.
"""

from collections.abc import Callable

from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext

# Type alias for guard predicates
Guard = Callable[[OrchestrationContext], bool]


def combat_just_started(ctx: OrchestrationContext) -> bool:
    """Check if combat just started (wasn't active before, but is now)."""
    return not ctx.flags.combat_was_active and ctx.game_state.combat.is_active


def combat_just_ended(ctx: OrchestrationContext) -> bool:
    """Check if combat just ended (was active before, but not now)."""
    return ctx.flags.combat_was_active and not ctx.game_state.combat.is_active


def has_npc_targets(ctx: OrchestrationContext) -> bool:
    """Check if the user message targets specific NPCs (e.g., @npc_name)."""
    return bool(ctx.flags.npc_targets)


def no_enemies_remaining(ctx: OrchestrationContext) -> bool:
    """Check if no active enemies remain in combat."""
    if not ctx.game_state.combat.is_active:
        return False

    return not any(p.is_active and p.faction == CombatFaction.ENEMY for p in ctx.game_state.combat.participants)


def is_player_turn(ctx: OrchestrationContext) -> bool:
    """Check if the current turn belongs to the player."""
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    return current_turn.is_player


def is_current_turn_npc_or_monster(ctx: OrchestrationContext) -> bool:
    """Check if current turn is ENEMY or NEUTRAL faction (should auto-continue)."""
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    return current_turn.faction in (CombatFaction.ENEMY, CombatFaction.NEUTRAL)


def combat_loop_should_continue(ctx: OrchestrationContext) -> bool:
    """Check if combat loop should continue (combat active, non-player/non-ally turn exists).

    The loop continues for ENEMY and NEUTRAL factions only.
    Player turns and ally turns exit the loop to wait for player input.
    """
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    # Continue loop only for NPC/monster auto-execution (ENEMY, NEUTRAL factions)
    # Stop for PLAYER (player action) and ALLY (awaiting manual input or suggestion request)
    return current_turn.faction in (CombatFaction.ENEMY, CombatFaction.NEUTRAL)
