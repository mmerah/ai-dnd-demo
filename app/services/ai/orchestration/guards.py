"""Guard predicates for conditional pipeline execution.

Guards are simple predicate functions that determine whether conditional steps
should execute. They inspect the OrchestrationContext and return a boolean.

Guards should be:
- Pure functions (no side effects)
- Fast (simple boolean logic)
- Well-named (clearly describe the condition)
- Testable with minimal context setup
"""

import logging
from collections.abc import Callable

from app.models.combat import CombatFaction
from app.services.ai.orchestration.context import OrchestrationContext

logger = logging.getLogger(__name__)

# Type alias for guard predicates
Guard = Callable[[OrchestrationContext], bool]


def combat_just_started(ctx: OrchestrationContext) -> bool:
    """Check if combat just started (wasn't active before, but is now).

    Args:
        ctx: Current orchestration context

    Returns:
        True if combat transitioned from inactive to active
    """
    result = not ctx.flags.combat_was_active and ctx.game_state.combat.is_active
    logger.debug(
        "Guard combat_just_started: combat_was_active=%s, is_active_now=%s -> %s",
        ctx.flags.combat_was_active,
        ctx.game_state.combat.is_active,
        result,
    )
    return result


def combat_just_ended(ctx: OrchestrationContext) -> bool:
    """Check if combat just ended (was active before, but not now).

    Args:
        ctx: Current orchestration context

    Returns:
        True if combat transitioned from active to inactive
    """
    result = ctx.flags.combat_was_active and not ctx.game_state.combat.is_active
    logger.debug(
        "Guard combat_just_ended: combat_was_active=%s, is_active_now=%s -> %s",
        ctx.flags.combat_was_active,
        ctx.game_state.combat.is_active,
        result,
    )
    return result


def has_npc_targets(ctx: OrchestrationContext) -> bool:
    """Check if the user message targets specific NPCs (e.g., @npc_name).

    Args:
        ctx: Current orchestration context

    Returns:
        True if NPC targets were detected in the message
    """
    result = bool(ctx.flags.npc_targets)
    logger.debug("Guard has_npc_targets: %s (targets=%s)", result, ctx.flags.npc_targets)
    return result


def no_enemies_remaining(ctx: OrchestrationContext) -> bool:
    """Check if no active enemies remain in combat.

    This guard is used by CombatAutoEnd to detect when combat should
    automatically end due to all enemies being defeated.

    Args:
        ctx: Current orchestration context

    Returns:
        True if combat is active and no enemies remain
    """
    if not ctx.game_state.combat.is_active:
        return False

    # Check if there are any active ENEMY faction participants
    # Replicates combat_service.should_auto_end_combat logic
    return not any(p.is_active and p.faction == CombatFaction.ENEMY for p in ctx.game_state.combat.participants)


def is_current_turn_ally(ctx: OrchestrationContext) -> bool:
    """Check if the current turn belongs to an ALLY faction combatant.

    This guard directly checks the combat state to determine if the current
    turn is an ally NPC.

    Args:
        ctx: Current orchestration context

    Returns:
        True if current turn is an ALLY faction combatant
    """
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    return current_turn.faction == CombatFaction.ALLY


def is_player_turn(ctx: OrchestrationContext) -> bool:
    """Check if the current turn belongs to the player.

    Args:
        ctx: Current orchestration context

    Returns:
        True if current turn is the player
    """
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    return current_turn.is_player


def is_current_turn_npc_or_monster(ctx: OrchestrationContext) -> bool:
    """Check if the current turn is an NPC or Monster that should auto-continue.

    This guard checks for non-player turns that should be automated (not ALLY faction).
    Excludes PLAYER faction and ALLY faction (which gets suggestions instead).

    Args:
        ctx: Current orchestration context

    Returns:
        True if current turn should auto-continue (ENEMY or NEUTRAL faction)
    """
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    # Auto-continue for ENEMY and NEUTRAL factions
    # (PLAYER and ALLY are handled differently)
    return current_turn.faction in (CombatFaction.ENEMY, CombatFaction.NEUTRAL)


def combat_loop_should_continue(ctx: OrchestrationContext) -> bool:
    """Check if the combat loop should continue iterating.

    This is the main guard for the combat auto-run loop. It returns True if:
    - Combat is active
    - Current turn exists
    - Turn is not a player turn

    The loop continues while this returns True, up to the safety cap.

    Note:
        ALLY turns ARE allowed in the loop to generate initial combat suggestions.
        The inner step (GenerateAllySuggestion) returns HALT to stop the loop after
        generating a suggestion, waiting for player input.

    Args:
        ctx: Current orchestration context

    Returns:
        True if loop should continue
    """
    if not ctx.game_state.combat.is_active:
        return False

    current_turn = ctx.game_state.combat.get_current_turn()
    if not current_turn:
        return False

    # Continue loop for all non-PLAYER turns
    # Inner steps will handle: auto-end, ally suggestions (with HALT), NPC/monster auto-continue
    return current_turn.faction != CombatFaction.PLAYER
